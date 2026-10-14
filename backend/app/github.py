"""Minimal GitHub REST client + webhook signature verification."""
import hashlib
import hmac
import re

import httpx

from . import config


class GitHubError(RuntimeError):
    pass


def verify_signature(secret: str, body: bytes, header: str | None) -> bool:
    """Constant-time check of GitHub's X-Hub-Signature-256 header."""
    if not secret or not header or not header.startswith("sha256="):
        return False
    expected = "sha256=" + hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, header)


def parse_pr_url(url: str) -> tuple[str, int]:
    m = re.search(r"github\.com/([\w.-]+/[\w.-]+)/pull/(\d+)", url)
    if not m:
        raise ValueError("Expected a URL like https://github.com/owner/repo/pull/123")
    return m.group(1), int(m.group(2))


class GitHubClient:
    def __init__(self, token: str | None = None, base: str | None = None):
        self.token = token if token is not None else config.GITHUB_TOKEN
        self.base = (base or config.GITHUB_API).rstrip("/")

    def _headers(self, accept: str = "application/vnd.github+json") -> dict:
        h = {"Accept": accept, "X-GitHub-Api-Version": "2022-11-28", "User-Agent": "pr-sentinel"}
        if self.token:
            h["Authorization"] = f"Bearer {self.token}"
        return h

    def _req(self, method: str, path: str, accept: str = "application/vnd.github+json", **kw):
        try:
            r = httpx.request(method, f"{self.base}{path}", headers=self._headers(accept),
                              timeout=30, **kw)
        except httpx.HTTPError as e:
            raise GitHubError(f"GitHub request failed: {e}") from e
        if r.status_code >= 400:
            raise GitHubError(f"GitHub {method} {path} -> {r.status_code}: {r.text[:300]}")
        return r

    def get_pr(self, repo: str, number: int) -> dict:
        return self._req("GET", f"/repos/{repo}/pulls/{number}").json()

    def get_diff(self, repo: str, number: int) -> str:
        return self._req("GET", f"/repos/{repo}/pulls/{number}",
                         accept="application/vnd.github.v3.diff").text

    def post_review(self, repo: str, number: int, sha: str, body: str, comments: list[dict]) -> None:
        """Post one PR review with inline comments. Falls back to a plain
        summary comment if GitHub rejects any inline position."""
        payload = {"commit_id": sha, "body": body, "event": "COMMENT", "comments": comments}
        try:
            self._req("POST", f"/repos/{repo}/pulls/{number}/reviews", json=payload)
        except GitHubError:
            if not comments:
                raise
            self._req("POST", f"/repos/{repo}/issues/{number}/comments", json={"body": body})
