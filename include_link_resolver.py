"""
Include-to-parent Learn URL resolver.

Motivation
----------
Learn documentation on `learn.microsoft.com` is assembled at build time from
"include" markdown fragments under `<repo>/articles/**/includes/*.md`. These
fragments do not have their own public Learn URL — if the LLM summarises a
patch that lives in an include file, `call_gpt.correct_links` currently
produces a URL like:

    https://learn.microsoft.com/en-us/azure/foundry/openai/includes/foo-content

which returns 404. Every such link in a Teams notification is unclickable.

This module resolves an include-file URL to the *parent* article that
`[!INCLUDE []]`s it, which is a real, public Learn page. Resolution uses
GitHub code search over MicrosoftDocs' docs repositories.

Design principles (do NOT change without care):

1. **Fail-open**: any exception, timeout, empty result, rate-limit, or
   missing token MUST fall back to returning the original URL unchanged.
   The main pipeline must never break because of the resolver.
2. **Cached**: in-memory LRU + optional file cache to avoid repeat
   GitHub API calls for the same include filename.
3. **Off by default**: controlled by env var `RESOLVE_INCLUDE_LINKS`.
4. **Rate-limit aware**: GitHub authenticated code search allows 30 req/min.
   The resolver counts calls per minute and short-circuits above the limit.
5. **Confidence gate**: if code search returns multiple parent candidates
   from different top-level "product" directories, the resolver keeps
   the candidate that matches the source repo of the include (never
   returns a random pick).

Public API
----------
- `IncludeLinkResolver(...)`: instantiate once per Spyder run.
- `resolver.rewrite_markdown(markdown_text)`: scan the markdown for Learn
  include URLs and replace each with the resolved parent URL, or leave
  it unchanged if resolution fails.

Not touching the main pipeline
------------------------------
If `RESOLVE_INCLUDE_LINKS != "true"`, `rewrite_markdown` returns the input
unchanged and never talks to GitHub.
"""
import json
import os
import re
import threading
import time
from collections import OrderedDict
from typing import Optional
from urllib.parse import quote, urlparse

import requests

from logs import logger


# -----------------------------------------------------------------------------
# Constants
# -----------------------------------------------------------------------------

# Only Learn URLs matching this shape are candidates for resolution.
# Example match:
#   https://learn.microsoft.com/en-us/azure/foundry/openai/includes/foo-content
LEARN_INCLUDE_URL_RE = re.compile(
    r"https?://learn\.microsoft\.com/[a-z]{2}-[a-z]{2}/azure/[^\s)\]}>\"']*?/includes/[^\s)\]}>\"']+",
    re.IGNORECASE,
)

# Map from top-level Azure "product root" (first path segment after /azure/)
# to the GitHub repo that owns its source. Determines which repo to search.
# Keep in sync with the front-end `docLinks.ts` list.
PRODUCT_ROOT_TO_REPO = {
    "foundry": "MicrosoftDocs/azure-ai-docs",
    "foundry-classic": "MicrosoftDocs/azure-ai-docs",
    "ai-services": "MicrosoftDocs/azure-ai-docs",
    "machine-learning": "MicrosoftDocs/azure-docs",
}

# GitHub Search API endpoint. Uses text-match search over file *contents*.
GITHUB_CODE_SEARCH_URL = "https://api.github.com/search/code"

# Rate limit: GitHub Search API allows 30 req/min for authenticated users.
# Stay comfortably below to leave headroom for other consumers of the token.
_RATE_LIMIT_MAX_PER_MINUTE = 20
_RATE_LIMIT_WINDOW_SECONDS = 60

# HTTP timeout for GitHub calls.
_REQUEST_TIMEOUT_SECONDS = 15

# Persistent cache file location; kept alongside `last_crawl_time.txt`.
DEFAULT_CACHE_PATH = "include_link_cache.json"


def _is_enabled() -> bool:
    """Feature toggle. Off unless env var explicitly set to a truthy value."""
    return os.getenv("RESOLVE_INCLUDE_LINKS", "").strip().lower() in ("true", "1", "yes")


# -----------------------------------------------------------------------------
# Pure helpers (no I/O — easy to unit test)
# -----------------------------------------------------------------------------

def parse_include_url(url: str) -> Optional[dict]:
    """Parse a Learn include URL into its constituent pieces.

    Returns a dict with keys::
        product_root  — e.g. "foundry"
        parent_path   — path segments *before* "/includes/", excluding /azure/
        include_slug  — the last path segment (the include filename minus .md)
        repo          — GitHub repo that owns the source (from PRODUCT_ROOT_TO_REPO)

    Returns None if the URL is not a supported include URL.
    """
    try:
        parsed = urlparse(url)
    except Exception:
        return None
    if parsed.hostname != "learn.microsoft.com":
        return None
    parts = [p for p in parsed.path.split("/") if p]
    # Expect: [<locale>, "azure", <product_root>, ..., "includes", <slug>]
    if len(parts) < 5:
        return None
    if not re.match(r"^[a-z]{2}-[a-z]{2}$", parts[0], re.IGNORECASE):
        return None
    if parts[1] != "azure":
        return None
    if "includes" not in parts:
        return None
    includes_idx = parts.index("includes")
    # Slug is right after 'includes'. If there's no slug, bail.
    if includes_idx + 1 >= len(parts):
        return None
    product_root = parts[2]
    repo = PRODUCT_ROOT_TO_REPO.get(product_root)
    if not repo:
        return None
    # parent_path = everything between /azure/ and /includes/ (exclusive)
    parent_path_parts = parts[2:includes_idx]  # includes product_root
    include_slug = parts[includes_idx + 1]
    # Strip anchors / anything odd
    include_slug = include_slug.split("#")[0]
    return {
        "product_root": product_root,
        "parent_path": "/".join(parent_path_parts),  # e.g. "foundry/openai"
        "include_slug": include_slug,                # e.g. "how-to-gpt-with-vision-content"
        "repo": repo,
    }


def github_path_to_learn_url(github_path: str, locale: str = "en-us") -> Optional[str]:
    """Convert a GitHub path like ``articles/foundry/openai/how-to/gpt-with-vision.md``
    into a public Learn URL. Returns None for paths that do not look like an
    Azure article (e.g. /includes/, /toc.yml, /breadcrumb/)."""
    if not github_path.startswith("articles/"):
        return None
    # Never re-promote another include file to a public URL.
    if "/includes/" in github_path or github_path.endswith("/toc.yml"):
        return None
    if not github_path.endswith(".md"):
        return None
    slug = github_path[len("articles/"):-len(".md")]
    return f"https://learn.microsoft.com/{locale}/azure/{slug}"


def choose_best_candidate(candidates: list, hint_parent_path: str) -> Optional[str]:
    """Pick the most-specific candidate github path given the parent_path hint.

    Preference order:
      1. Path that starts with the same parent_path (e.g. foundry/openai/*)
         and is not itself an include or partner file.
      2. Any candidate that starts with the same product_root.
      3. None — better to fall back than misattribute.

    ``candidates`` is a list of github paths (strings).
    """
    same_parent = [
        p for p in candidates
        if p.startswith(f"articles/{hint_parent_path}/") and "/includes/" not in p
    ]
    if len(same_parent) == 1:
        return same_parent[0]
    if len(same_parent) > 1:
        # Prefer shortest path (usually the concept/how-to file, not deeper artifacts).
        return sorted(same_parent, key=lambda p: (len(p.split("/")), p))[0]

    # Fallback: same product_root only. Only accept if unambiguous.
    product_root = hint_parent_path.split("/")[0]
    same_root = [
        p for p in candidates
        if p.startswith(f"articles/{product_root}/") and "/includes/" not in p
    ]
    if len(same_root) == 1:
        return same_root[0]
    return None


# -----------------------------------------------------------------------------
# Resolver (I/O + cache + rate limit)
# -----------------------------------------------------------------------------

class IncludeLinkResolver:
    """Resolve `/includes/` Learn URLs to parent article Learn URLs.

    The resolver is safe to call from the main pipeline: on any error it
    returns the original URL unchanged. Enable via env var
    ``RESOLVE_INCLUDE_LINKS=true``.
    """

    def __init__(
        self,
        github_token: Optional[str] = None,
        cache_path: Optional[str] = DEFAULT_CACHE_PATH,
        enabled: Optional[bool] = None,
    ):
        self._enabled = _is_enabled() if enabled is None else bool(enabled)
        self._token = github_token if github_token is not None else os.getenv("PERSONAL_TOKEN")
        self._cache_path = cache_path
        # In-memory cache: key -> resolved_url_or_None
        self._memory_cache: "OrderedDict[str, Optional[str]]" = OrderedDict()
        self._memory_cache_max = 500
        self._lock = threading.Lock()
        # Rate-limit tracker: list of unix timestamps of recent calls
        self._call_timestamps: list = []
        # Load persistent cache
        self._load_persistent_cache()

    # -- cache -----------------------------------------------------------------

    def _cache_key(self, parsed: dict) -> str:
        return f"{parsed['repo']}::{parsed['parent_path']}::{parsed['include_slug']}"

    def _load_persistent_cache(self) -> None:
        if not self._cache_path or not os.path.exists(self._cache_path):
            return
        try:
            with open(self._cache_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, dict):
                for k, v in data.items():
                    if not isinstance(k, str):
                        continue
                    if v is not None and not isinstance(v, str):
                        continue
                    self._memory_cache[k] = v
                logger.info(
                    "IncludeLinkResolver: loaded %d cache entries from %s",
                    len(self._memory_cache), self._cache_path,
                )
        except Exception as exc:
            logger.warning("IncludeLinkResolver: cache load failed (%s); ignoring", exc)

    def _persist_cache(self) -> None:
        if not self._cache_path:
            return
        try:
            with open(self._cache_path, "w", encoding="utf-8") as f:
                json.dump(dict(self._memory_cache), f, ensure_ascii=False, indent=2)
        except Exception as exc:
            logger.warning("IncludeLinkResolver: cache persist failed (%s)", exc)

    def _cache_put(self, key: str, value: Optional[str]) -> None:
        with self._lock:
            if key in self._memory_cache:
                self._memory_cache.move_to_end(key)
            self._memory_cache[key] = value
            while len(self._memory_cache) > self._memory_cache_max:
                self._memory_cache.popitem(last=False)
        # Persist opportunistically; failures are non-fatal.
        self._persist_cache()

    # -- rate limit ------------------------------------------------------------

    def _rate_limit_ok(self) -> bool:
        now = time.time()
        cutoff = now - _RATE_LIMIT_WINDOW_SECONDS
        with self._lock:
            self._call_timestamps = [t for t in self._call_timestamps if t > cutoff]
            if len(self._call_timestamps) >= _RATE_LIMIT_MAX_PER_MINUTE:
                return False
            self._call_timestamps.append(now)
            return True

    # -- github search --------------------------------------------------------

    def _search_github(self, parsed: dict) -> Optional[str]:
        """Return a github path (e.g. ``articles/foundry/openai/how-to/gpt-with-vision.md``)
        that includes the given include file, or None on any failure."""
        include_slug = parsed["include_slug"]
        repo = parsed["repo"]
        # GitHub search query: files in the repo whose contents contain the
        # slug and are markdown, excluding the include file itself.
        # We match on the filename portion — this is unique enough in practice.
        query = f'repo:{repo} "{include_slug}" in:file extension:md'
        headers = {
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }
        if self._token:
            headers["Authorization"] = f"Bearer {self._token}"
        try:
            resp = requests.get(
                GITHUB_CODE_SEARCH_URL,
                params={"q": query, "per_page": 10},
                headers=headers,
                timeout=_REQUEST_TIMEOUT_SECONDS,
            )
        except requests.RequestException as exc:
            logger.warning("IncludeLinkResolver: GitHub request failed: %s", exc)
            return None
        if resp.status_code == 403 and "rate limit" in resp.text.lower():
            logger.warning("IncludeLinkResolver: hit GitHub rate limit; skipping resolution")
            return None
        if resp.status_code != 200:
            logger.warning(
                "IncludeLinkResolver: GitHub search returned %s for %s",
                resp.status_code, include_slug,
            )
            return None
        try:
            body = resp.json()
        except ValueError:
            logger.warning("IncludeLinkResolver: could not parse GitHub JSON response")
            return None
        items = body.get("items", []) if isinstance(body, dict) else []
        paths = [it.get("path", "") for it in items if isinstance(it, dict)]
        paths = [p for p in paths if p]
        # Exclude the include file itself.
        include_filename = f"{include_slug}.md"
        paths = [p for p in paths if not p.endswith(f"/includes/{include_filename}")]
        return choose_best_candidate(paths, parsed["parent_path"])

    # -- public API -----------------------------------------------------------

    def resolve_single(self, url: str) -> str:
        """Given a Learn `/includes/` URL, return the parent Learn URL if we
        can determine it. Return the original ``url`` on any failure so
        callers are guaranteed a safe fall-through."""
        if not self._enabled:
            return url
        try:
            parsed = parse_include_url(url)
        except Exception:
            return url
        if not parsed:
            return url
        key = self._cache_key(parsed)
        # Cache lookup
        with self._lock:
            if key in self._memory_cache:
                cached = self._memory_cache[key]
                # cached == None means "we tried, we failed" — respect that
                # for the session and fall back to original URL.
                return cached if cached else url
        # Rate limit check
        if not self._rate_limit_ok():
            return url
        # Network call (may return None)
        github_path = None
        try:
            github_path = self._search_github(parsed)
        except Exception as exc:
            # Absolutely nothing should propagate.
            logger.warning("IncludeLinkResolver: unexpected error resolving %s: %s", url, exc)
            self._cache_put(key, None)
            return url
        if not github_path:
            self._cache_put(key, None)
            return url
        # Derive locale from original URL for a nicer result (keep same lang)
        locale = "en-us"
        try:
            first_seg = urlparse(url).path.split("/")[1]
            if re.match(r"^[a-z]{2}-[a-z]{2}$", first_seg, re.IGNORECASE):
                locale = first_seg.lower()
        except Exception:
            pass
        resolved = github_path_to_learn_url(github_path, locale=locale)
        if not resolved:
            self._cache_put(key, None)
            return url
        self._cache_put(key, resolved)
        logger.info("IncludeLinkResolver: %s -> %s", url, resolved)
        return resolved

    def rewrite_markdown(self, markdown_text: str) -> str:
        """Scan ``markdown_text`` for Learn include URLs and replace each with
        the resolved parent URL if resolution succeeds. Otherwise leave the
        URL unchanged.

        This method is safe to call unconditionally: if the feature is
        disabled, no scanning happens and the input is returned as-is."""
        if not self._enabled or not isinstance(markdown_text, str) or not markdown_text:
            return markdown_text
        # Collect the set of URLs first so we do at most one lookup per URL,
        # even if it appears multiple times.
        try:
            urls = set(LEARN_INCLUDE_URL_RE.findall(markdown_text))
        except Exception:
            return markdown_text
        if not urls:
            return markdown_text
        # Resolve each; only apply replacements where resolution changed.
        replacements = {}
        for url in urls:
            resolved = self.resolve_single(url)
            if resolved and resolved != url:
                replacements[url] = resolved
        if not replacements:
            return markdown_text
        out = markdown_text
        for old, new in replacements.items():
            out = out.replace(old, new)
        return out
