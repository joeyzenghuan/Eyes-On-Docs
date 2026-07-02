"""
Unit tests for CommitFetcher URL path parsing.

Purpose: guard against regressions in `CommitFetcher.get_all_commits`'s
path-extraction logic — specifically that `topic_path` is extracted correctly
regardless of query-string parameter order and presence of extra params such
as `sha=live`.

These tests are pure-function checks: they exercise only the URL parsing
branch of `get_all_commits`, so no GitHub API call is made.
Run: `python -m pytest test/test_commit_fetch_path_parse.py -v`
"""
import os
import sys
from unittest.mock import patch

# Allow running the test from the repo root or the test directory
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from commit_fetch import CommitFetcher


def _extract_topic_path(url):
    """Call get_all_commits far enough to compute topic_path, then bail out."""
    fetcher = CommitFetcher()
    # Short-circuit the HTTP call so we only exercise the parsing logic.
    with patch.object(CommitFetcher, '_make_request_to_json', return_value=[]):
        fetcher.get_all_commits(url, headers={})
    return fetcher.topic_path


def test_path_only():
    """Baseline: existing config format with only ?path= param."""
    url = "https://api.github.com/repos/MicrosoftDocs/azure-docs/commits?path=articles/ai-services/openai"
    assert _extract_topic_path(url) == "articles/ai-services/openai"


def test_path_with_trailing_slash():
    """Trailing slash on path should be preserved (matches existing configs)."""
    url = "https://api.github.com/repos/MicrosoftDocs/azure-docs/commits?path=articles/ai-services/openai/"
    assert _extract_topic_path(url) == "articles/ai-services/openai/"


def test_path_then_sha():
    """pr repo case: ?path=X&sha=live must NOT swallow &sha=live into topic_path."""
    url = "https://api.github.com/repos/MicrosoftDocs/azure-ai-docs-pr/commits?path=articles/foundry/openai&sha=live"
    assert _extract_topic_path(url) == "articles/foundry/openai"


def test_sha_then_path():
    """Query-param order should not matter."""
    url = "https://api.github.com/repos/MicrosoftDocs/azure-ai-docs-pr/commits?sha=live&path=articles/foundry/openai"
    assert _extract_topic_path(url) == "articles/foundry/openai"


def test_path_and_multiple_extra_params():
    """Multiple extra params (sha, per_page, since) should all be ignored."""
    url = (
        "https://api.github.com/repos/MicrosoftDocs/azure-ai-docs-pr/commits"
        "?path=articles/foundry/openai&sha=live&per_page=100&since=2026-06-01T00:00:00Z"
    )
    assert _extract_topic_path(url) == "articles/foundry/openai"


def test_no_query_string():
    """URL without any query string yields None (backward compatible)."""
    url = "https://api.github.com/repos/MicrosoftDocs/azure-docs/commits"
    assert _extract_topic_path(url) is None


def test_only_other_params_no_path():
    """URL with query but no path param yields None."""
    url = "https://api.github.com/repos/MicrosoftDocs/azure-docs/commits?sha=live"
    assert _extract_topic_path(url) is None


if __name__ == "__main__":
    # Allow running as a plain script too: `python test/test_commit_fetch_path_parse.py`
    import traceback
    tests = [
        test_path_only,
        test_path_with_trailing_slash,
        test_path_then_sha,
        test_sha_then_path,
        test_path_and_multiple_extra_params,
        test_no_query_string,
        test_only_other_params_no_path,
    ]
    failed = 0
    for t in tests:
        try:
            t()
            print(f"PASS  {t.__name__}")
        except AssertionError:
            failed += 1
            print(f"FAIL  {t.__name__}")
            traceback.print_exc()
    if failed:
        sys.exit(1)
    print(f"\nAll {len(tests)} tests passed.")
