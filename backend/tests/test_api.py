import hashlib
import hmac
import json

import pytest
from fastapi.testclient import TestClient

from app import config, main
from app.github import GitHubClient, parse_pr_url, verify_signature
from app.llm import FakeClient

GOOD = {"summary": "s", "findings": [
    {"line": 11, "severity": "high", "category": "security", "title": "SQLi", "message": "bad"}]}
SECRET = "topsecret"


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setattr(main, "get_client", lambda: FakeClient(GOOD))
    monkeypatch.setattr(config, "GITHUB_WEBHOOK_SECRET", SECRET)
    return TestClient(main.app)


def sign(body: bytes, secret=SECRET) -> str:
    return "sha256=" + hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()


def test_signature_verification():
    body = b'{"a":1}'
    assert verify_signature(SECRET, body, sign(body))
    assert not verify_signature(SECRET, body, sign(body, "wrong"))
    assert not verify_signature(SECRET, body, None)
    assert not verify_signature("", body, sign(body, ""))  # unset secret never validates


def test_parse_pr_url():
    assert parse_pr_url("https://github.com/o/r/pull/42") == ("o/r", 42)
    with pytest.raises(ValueError):
        parse_pr_url("https://example.com/nope")


def test_health(client):
    assert client.get("/api/health").json()["status"] == "ok"


def test_playground_review_persists_and_shows_in_dashboard(client, sample_diff):
    r = client.post("/api/review/diff", json={"diff": sample_diff})
    assert r.status_code == 200 and r.json()["findings"][0]["title"] == "SQLi"
    listing = client.get("/api/reviews").json()
    assert len(listing) == 1 and listing[0]["finding_count"] == 1
    detail = client.get(f"/api/reviews/{listing[0]['id']}").json()
    assert detail["findings"][0]["file"] == "app/auth.py"
    s = client.get("/api/stats").json()
    assert s["reviews"] == 1 and s["by_severity"] == {"high": 1}
    assert client.get("/api/reviews/999").status_code == 404


def test_empty_diff_rejected(client):
    assert client.post("/api/review/diff", json={"diff": ""}).status_code == 422


def test_webhook_rejects_bad_signature(client):
    body = b"{}"
    r = client.post("/api/webhooks/github", content=body,
                    headers={"X-Hub-Signature-256": "sha256=bad", "X-GitHub-Event": "ping"})
    assert r.status_code == 401


def test_webhook_ping_and_ignored_events(client):
    body = b"{}"
    h = {"X-Hub-Signature-256": sign(body), "X-GitHub-Event": "ping"}
    assert client.post("/api/webhooks/github", content=body, headers=h).json()["pong"]
    h["X-GitHub-Event"] = "push"
    assert client.post("/api/webhooks/github", content=body, headers=h).json()["ignored"] == "push"


def test_webhook_queues_pr_review(client, monkeypatch):
    calls = []
    monkeypatch.setattr(main, "review_pull_request", lambda repo, n, llm, **kw: calls.append((repo, n)))
    payload = {"action": "opened", "pull_request": {"number": 7, "draft": False},
               "repository": {"full_name": "o/r"}}
    body = json.dumps(payload).encode()
    r = client.post("/api/webhooks/github", content=body,
                    headers={"X-Hub-Signature-256": sign(body), "X-GitHub-Event": "pull_request"})
    assert r.json() == {"ok": True, "queued": "o/r#7"}
    assert calls == [("o/r", 7)]  # TestClient runs background tasks before returning


def test_webhook_ignores_drafts_and_closed(client):
    for payload in (
        {"action": "opened", "pull_request": {"number": 1, "draft": True}, "repository": {"full_name": "o/r"}},
        {"action": "closed", "pull_request": {"number": 1}, "repository": {"full_name": "o/r"}},
    ):
        body = json.dumps(payload).encode()
        r = client.post("/api/webhooks/github", content=body,
                        headers={"X-Hub-Signature-256": sign(body), "X-GitHub-Event": "pull_request"})
        assert "ignored" in r.json()


class StubGH(GitHubClient):
    def __init__(self, diff):
        self.diff, self.posted = diff, None

    def get_pr(self, repo, number):
        return {"head": {"sha": "abc123"}, "title": "Add login"}

    def get_diff(self, repo, number):
        return self.diff

    def post_review(self, repo, number, sha, body, comments):
        self.posted = (sha, body, comments)


def test_pipeline_posts_inline_comments_and_is_idempotent(sample_diff):
    from app.pipeline import review_pull_request
    gh = StubGH(sample_diff)
    res = review_pull_request("o/r", 3, FakeClient(GOOD), gh)
    sha, body, comments = gh.posted
    assert sha == "abc123" and comments[0]["path"] == "app/auth.py" and comments[0]["line"] == 11
    assert "score" in body
    again = review_pull_request("o/r", 3, FakeClient(GOOD), gh)
    assert again["skipped"] is True
    assert review_pull_request("o/r", 3, FakeClient(GOOD), gh, force=True)["skipped"] is False


def test_rules_mode_needs_no_model(sample_diff, monkeypatch):
    def boom():
        raise AssertionError("model must not be used in rules mode")
    monkeypatch.setattr(main, "get_client", boom)
    c = TestClient(main.app)
    r = c.post("/api/review/diff", json={"diff": sample_diff, "mode": "rules"})
    assert r.status_code == 200
    body = r.json()
    assert body["model"] == "rules-only"
    assert {"Possible SQL injection", "Hardcoded secret"} <= {f["title"] for f in body["findings"]}
    assert c.post("/api/review/diff", json={"diff": sample_diff, "mode": "x"}).status_code == 422
