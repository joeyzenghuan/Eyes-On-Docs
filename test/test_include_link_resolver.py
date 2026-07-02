"""
Tests for include_link_resolver.

Split into two parts:
  A. Pure-function tests (parse / mapping / candidate selection) — no I/O.
  B. Resolver tests with `requests.get` mocked — no real GitHub call.

Run: `python -m pytest test/test_include_link_resolver.py -v`
  or: `python test/test_include_link_resolver.py`
"""
import json
import os
import sys
import tempfile
from unittest.mock import patch, MagicMock

# Make the top-level module importable when run from either dir.
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from include_link_resolver import (
    IncludeLinkResolver,
    choose_best_candidate,
    github_path_to_learn_url,
    parse_include_url,
    LEARN_INCLUDE_URL_RE,
)


# =============================================================================
# A. Pure-function tests
# =============================================================================

# --- parse_include_url -------------------------------------------------------

def test_parse_valid_foundry_openai_include():
    r = parse_include_url(
        "https://learn.microsoft.com/en-us/azure/foundry/openai/includes/how-to-gpt-with-vision-content"
    )
    assert r == {
        "product_root": "foundry",
        "parent_path": "foundry/openai",
        "include_slug": "how-to-gpt-with-vision-content",
        "repo": "MicrosoftDocs/azure-ai-docs",
    }


def test_parse_valid_foundry_agents_include():
    r = parse_include_url(
        "https://learn.microsoft.com/en-us/azure/foundry/agents/includes/concepts-standard-agent-setup-content"
    )
    assert r["parent_path"] == "foundry/agents"
    assert r["include_slug"] == "concepts-standard-agent-setup-content"


def test_parse_valid_direct_under_product_root_include():
    """URL where /includes/ is directly under the product root (no sub-path)."""
    r = parse_include_url(
        "https://learn.microsoft.com/en-us/azure/foundry/includes/how-to-upgrade-azure-openai-2"
    )
    assert r["parent_path"] == "foundry"
    assert r["include_slug"] == "how-to-upgrade-azure-openai-2"


def test_parse_unknown_product_root_returns_none():
    """Products not in PRODUCT_ROOT_TO_REPO are not resolvable."""
    assert parse_include_url(
        "https://learn.microsoft.com/en-us/azure/some-unknown-product/includes/foo"
    ) is None


def test_parse_wrong_host_returns_none():
    assert parse_include_url(
        "https://example.com/en-us/azure/foundry/includes/foo"
    ) is None


def test_parse_no_includes_segment_returns_none():
    assert parse_include_url(
        "https://learn.microsoft.com/en-us/azure/foundry/openai/how-to/gpt-with-vision"
    ) is None


def test_parse_missing_locale_returns_none():
    assert parse_include_url(
        "https://learn.microsoft.com/azure/foundry/openai/includes/foo"
    ) is None


def test_parse_url_with_trailing_anchor():
    """Anchor in slug should be stripped, not included in cache key."""
    r = parse_include_url(
        "https://learn.microsoft.com/en-us/azure/foundry/openai/includes/foo-content#some-anchor"
    )
    assert r is not None
    assert r["include_slug"] == "foo-content"


def test_parse_garbage_input():
    """Bad input must not raise."""
    for bad in [None, "", "not-a-url", "http://", 12345]:
        try:
            r = parse_include_url(bad)  # type: ignore
        except Exception:
            raise AssertionError(f"parse_include_url raised on {bad!r}")
        assert r is None


# --- github_path_to_learn_url ------------------------------------------------

def test_github_path_to_learn_url_valid():
    assert github_path_to_learn_url("articles/foundry/openai/how-to/gpt-with-vision.md") == \
        "https://learn.microsoft.com/en-us/azure/foundry/openai/how-to/gpt-with-vision"


def test_github_path_to_learn_url_respects_locale():
    assert github_path_to_learn_url(
        "articles/foundry/openai/how-to/gpt-with-vision.md", locale="zh-cn"
    ) == "https://learn.microsoft.com/zh-cn/azure/foundry/openai/how-to/gpt-with-vision"


def test_github_path_include_file_returns_none():
    """Must never re-promote an include file to a public URL."""
    assert github_path_to_learn_url(
        "articles/foundry/openai/includes/foo-content.md"
    ) is None


def test_github_path_toc_returns_none():
    assert github_path_to_learn_url("articles/foundry/openai/toc.yml") is None


def test_github_path_non_articles_returns_none():
    """Some repos put breadcrumbs elsewhere; only articles/* is valid here."""
    assert github_path_to_learn_url("breadcrumb/toc.yml") is None
    assert github_path_to_learn_url("bundle/") is None


# --- choose_best_candidate ---------------------------------------------------

def test_choose_single_matching_parent():
    r = choose_best_candidate(
        ["articles/foundry/openai/how-to/gpt-with-vision.md"],
        hint_parent_path="foundry/openai",
    )
    assert r == "articles/foundry/openai/how-to/gpt-with-vision.md"


def test_choose_prefers_same_parent_over_sibling_repo_dir():
    """foundry vs foundry-classic must not be confused."""
    r = choose_best_candidate(
        [
            "articles/foundry-classic/openai/how-to/foo.md",
            "articles/foundry/openai/how-to/foo.md",
        ],
        hint_parent_path="foundry/openai",
    )
    assert r == "articles/foundry/openai/how-to/foo.md"


def test_choose_multiple_same_parent_picks_shortest():
    r = choose_best_candidate(
        [
            "articles/foundry/openai/how-to/very/deeply/nested/foo.md",
            "articles/foundry/openai/how-to/foo.md",
        ],
        hint_parent_path="foundry/openai",
    )
    assert r == "articles/foundry/openai/how-to/foo.md"


def test_choose_returns_none_when_ambiguous_across_products():
    """Ambiguous → prefer fallback (return None), never guess."""
    r = choose_best_candidate(
        [
            "articles/foundry-classic/openai/x.md",
            "articles/ai-services/openai/x.md",
        ],
        hint_parent_path="foundry/openai",
    )
    assert r is None


def test_choose_skips_include_file_matches():
    """The candidate list may include the include file itself; skip it."""
    r = choose_best_candidate(
        [
            "articles/foundry/openai/includes/foo-content.md",  # self
            "articles/foundry/openai/how-to/foo.md",             # parent
        ],
        hint_parent_path="foundry/openai",
    )
    assert r == "articles/foundry/openai/how-to/foo.md"


def test_choose_empty_list_returns_none():
    assert choose_best_candidate([], hint_parent_path="foundry/openai") is None


# --- URL regex --------------------------------------------------------------

def test_url_regex_finds_include_urls_in_markdown():
    md = """
Some summary text here.
See https://learn.microsoft.com/en-us/azure/foundry/openai/includes/how-to-gpt-with-vision-content
Also https://learn.microsoft.com/en-us/azure/foundry/agents/concepts/hosted-agent-permissions
And a wrong one https://example.com/foo/includes/bar
"""
    matches = LEARN_INCLUDE_URL_RE.findall(md)
    assert len(matches) == 1
    assert matches[0].endswith("how-to-gpt-with-vision-content")


# =============================================================================
# B. Resolver tests with mocked GitHub API
# =============================================================================

def _mk_resp(status: int, items=None, text: str = ""):
    mock = MagicMock()
    mock.status_code = status
    mock.text = text
    mock.json.return_value = {"items": [{"path": p} for p in (items or [])]}
    return mock


def _mk_resolver(**kwargs):
    """Build a resolver with feature enabled and no persistent cache."""
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".json")
    tmp.close()
    os.unlink(tmp.name)
    defaults = {"enabled": True, "github_token": "test-token", "cache_path": tmp.name}
    defaults.update(kwargs)
    return IncludeLinkResolver(**defaults), tmp.name


def test_disabled_resolver_returns_input_unchanged():
    r = IncludeLinkResolver(enabled=False, github_token=None, cache_path=None)
    url = "https://learn.microsoft.com/en-us/azure/foundry/openai/includes/foo-content"
    with patch("include_link_resolver.requests.get") as mock_get:
        assert r.resolve_single(url) == url
        assert r.rewrite_markdown(f"see {url}") == f"see {url}"
        assert not mock_get.called, "disabled resolver must not call GitHub"


def test_resolve_single_success_maps_to_parent():
    r, cache_path = _mk_resolver()
    try:
        url = "https://learn.microsoft.com/en-us/azure/foundry/openai/includes/how-to-gpt-with-vision-content"
        expected = "https://learn.microsoft.com/en-us/azure/foundry/openai/how-to/gpt-with-vision"
        mocked = _mk_resp(200, items=[
            "articles/foundry/openai/how-to/gpt-with-vision.md",
            "articles/foundry-classic/openai/how-to/gpt-with-vision.md",
            "articles/foundry/openai/includes/how-to-gpt-with-vision-content.md",  # self
        ])
        with patch("include_link_resolver.requests.get", return_value=mocked) as mock_get:
            out = r.resolve_single(url)
        assert out == expected
        assert mock_get.call_count == 1
        # Second call should hit cache — no additional GitHub request.
        with patch("include_link_resolver.requests.get") as mock_get2:
            out2 = r.resolve_single(url)
        assert out2 == expected
        assert mock_get2.call_count == 0
    finally:
        if os.path.exists(cache_path):
            os.unlink(cache_path)


def test_resolve_single_falls_back_on_403_rate_limit():
    r, cache_path = _mk_resolver()
    try:
        url = "https://learn.microsoft.com/en-us/azure/foundry/openai/includes/foo-content"
        mocked = _mk_resp(403, text="API rate limit exceeded")
        with patch("include_link_resolver.requests.get", return_value=mocked):
            out = r.resolve_single(url)
        # Rate-limit fall-back returns the original URL, does NOT cache a
        # negative result (we might succeed later this session once the limit resets).
        assert out == url
    finally:
        if os.path.exists(cache_path):
            os.unlink(cache_path)


def test_resolve_single_falls_back_on_network_error():
    import requests as _r
    r, cache_path = _mk_resolver()
    try:
        url = "https://learn.microsoft.com/en-us/azure/foundry/openai/includes/foo-content"
        with patch("include_link_resolver.requests.get",
                   side_effect=_r.ConnectionError("boom")):
            out = r.resolve_single(url)
        assert out == url
    finally:
        if os.path.exists(cache_path):
            os.unlink(cache_path)


def test_resolve_single_falls_back_on_no_candidates():
    r, cache_path = _mk_resolver()
    try:
        url = "https://learn.microsoft.com/en-us/azure/foundry/openai/includes/mystery-content"
        mocked = _mk_resp(200, items=[
            # Only the include file itself; no parent found.
            "articles/foundry/openai/includes/mystery-content.md",
        ])
        with patch("include_link_resolver.requests.get", return_value=mocked):
            out = r.resolve_single(url)
        assert out == url
        # Negative cached so we don't re-query
        with patch("include_link_resolver.requests.get") as mock_get2:
            out2 = r.resolve_single(url)
        assert out2 == url
        assert mock_get2.call_count == 0
    finally:
        if os.path.exists(cache_path):
            os.unlink(cache_path)


def test_resolve_single_falls_back_on_ambiguous():
    r, cache_path = _mk_resolver()
    try:
        url = "https://learn.microsoft.com/en-us/azure/foundry/openai/includes/foo-content"
        mocked = _mk_resp(200, items=[
            "articles/foundry-classic/openai/x.md",
            "articles/ai-services/openai/x.md",
        ])
        with patch("include_link_resolver.requests.get", return_value=mocked):
            out = r.resolve_single(url)
        # Ambiguous cross-product match → keep original URL.
        assert out == url
    finally:
        if os.path.exists(cache_path):
            os.unlink(cache_path)


def test_rewrite_markdown_replaces_only_include_urls():
    r, cache_path = _mk_resolver()
    try:
        include_url = "https://learn.microsoft.com/en-us/azure/foundry/openai/includes/how-to-gpt-with-vision-content"
        good_url = "https://learn.microsoft.com/en-us/azure/foundry/agents/concepts/hosted-agent-permissions"
        github_url = "https://github.com/example/repo"
        md = f"""
Some **update**. See [include]({include_url}) and [normal]({good_url}).
Random link {github_url}.
"""
        mocked = _mk_resp(200, items=[
            "articles/foundry/openai/how-to/gpt-with-vision.md",
        ])
        with patch("include_link_resolver.requests.get", return_value=mocked):
            out = r.rewrite_markdown(md)
        # include URL got rewritten
        assert include_url not in out
        assert "articles/foundry/openai/how-to/gpt-with-vision.md" not in out  # only URL, not raw path
        assert "learn.microsoft.com/en-us/azure/foundry/openai/how-to/gpt-with-vision" in out
        # non-include URLs unchanged
        assert good_url in out
        assert github_url in out
    finally:
        if os.path.exists(cache_path):
            os.unlink(cache_path)


def test_rewrite_markdown_empty_and_non_string_safe():
    r, cache_path = _mk_resolver()
    try:
        assert r.rewrite_markdown("") == ""
        assert r.rewrite_markdown(None) is None  # type: ignore
        # non-string input must not raise
        for bad in [123, {"a": 1}, ["x"]]:
            got = r.rewrite_markdown(bad)  # type: ignore
            assert got == bad
    finally:
        if os.path.exists(cache_path):
            os.unlink(cache_path)


def test_rate_limit_short_circuit():
    """Once we hit the per-minute limit, further calls return input unchanged
    without a network request."""
    r, cache_path = _mk_resolver()
    try:
        # Preload the timestamp buffer to simulate exhausted quota.
        import time as _t
        now = _t.time()
        # Fill with 20 recent timestamps (matches _RATE_LIMIT_MAX_PER_MINUTE).
        with r._lock:
            r._call_timestamps = [now - 1 for _ in range(20)]
        url = "https://learn.microsoft.com/en-us/azure/foundry/openai/includes/foo-content"
        with patch("include_link_resolver.requests.get") as mock_get:
            out = r.resolve_single(url)
        assert out == url
        assert not mock_get.called
    finally:
        if os.path.exists(cache_path):
            os.unlink(cache_path)


def test_persistent_cache_roundtrip():
    """Positive resolution should be persisted to disk and reloaded next run."""
    fd, path = tempfile.mkstemp(suffix=".json")
    os.close(fd)
    os.unlink(path)  # start clean
    try:
        r1 = IncludeLinkResolver(enabled=True, github_token="tok", cache_path=path)
        url = "https://learn.microsoft.com/en-us/azure/foundry/openai/includes/how-to-gpt-with-vision-content"
        mocked = _mk_resp(200, items=["articles/foundry/openai/how-to/gpt-with-vision.md"])
        with patch("include_link_resolver.requests.get", return_value=mocked):
            r1.resolve_single(url)
        # File should now exist with the mapping.
        with open(path, "r", encoding="utf-8") as f:
            saved = json.load(f)
        assert any("gpt-with-vision" in v for v in saved.values() if v)
        # New resolver instance should load the cache and never hit GitHub.
        r2 = IncludeLinkResolver(enabled=True, github_token="tok", cache_path=path)
        with patch("include_link_resolver.requests.get") as mock_get:
            out = r2.resolve_single(url)
        assert "how-to/gpt-with-vision" in out
        assert mock_get.call_count == 0
    finally:
        if os.path.exists(path):
            os.unlink(path)


# =============================================================================
# CLI runner
# =============================================================================

if __name__ == "__main__":
    import traceback
    tests = [obj for name, obj in list(globals().items()) if name.startswith("test_") and callable(obj)]
    failed = 0
    for t in tests:
        try:
            t()
            print(f"PASS  {t.__name__}")
        except AssertionError:
            failed += 1
            print(f"FAIL  {t.__name__}")
            traceback.print_exc()
        except Exception:
            failed += 1
            print(f"ERROR {t.__name__}")
            traceback.print_exc()
    if failed:
        sys.exit(1)
    print(f"\nAll {len(tests)} tests passed.")
