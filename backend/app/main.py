import json
import logging

import httpx
from fastapi import BackgroundTasks, FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from . import config, db
from .github import GitHubError, parse_pr_url, verify_signature
from .llm import LLMError, RulesOnlyClient, get_client
from .pipeline import review_pull_request
from .reviewer import review_diff

log = logging.getLogger("pr-sentinel")
app = FastAPI(title="PR Sentinel", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.FRONTEND_ORIGINS,
    allow_methods=["*"],
    allow_headers=["*"],
)

HANDLED_ACTIONS = {"opened", "synchronize", "reopened", "ready_for_review"}


class DiffRequest(BaseModel):
    diff: str = Field(min_length=1, max_length=200_000)
    min_severity: str = "low"
    mode: str = Field(default="ai", pattern="^(ai|rules)$")  # rules = instant, no model


class PRRequest(BaseModel):
    url: str
    post: bool = False  # manual runs don't comment on the PR unless asked


def _ollama_up() -> bool:
    try:
        return httpx.get(f"{config.OLLAMA_URL}/api/tags", timeout=2).status_code == 200
    except httpx.HTTPError:
        return False


@app.get("/api/health")
def health():
    return {
        "status": "ok",
        "provider": config.LLM_PROVIDER,
        "model": config.CHAT_MODEL if config.LLM_PROVIDER == "ollama" else None,
        "llm_ready": _ollama_up() if config.LLM_PROVIDER == "ollama" else True,
        "github_token": bool(config.GITHUB_TOKEN),
        "webhook_secret": bool(config.GITHUB_WEBHOOK_SECRET),
    }


@app.post("/api/review/diff")
def review_raw_diff(req: DiffRequest):
    try:
        if req.mode == "rules":
            result = review_diff(req.diff, RulesOnlyClient(), req.min_severity, use_rules=True)
        else:
            result = review_diff(req.diff, get_client(), req.min_severity)
    except LLMError as e:
        raise HTTPException(502, str(e))
    data = result.as_dict()
    db.save_review(data, source="playground")
    return data


@app.post("/api/review/pr")
def review_pr(req: PRRequest):
    try:
        repo, number = parse_pr_url(req.url)
        return review_pull_request(repo, number, get_client(), post=req.post, source="manual")
    except ValueError as e:
        raise HTTPException(400, str(e))
    except (GitHubError, LLMError) as e:
        raise HTTPException(502, str(e))


def _run_webhook_review(repo: str, number: int) -> None:
    try:
        review_pull_request(repo, number, get_client(), post=True, source="webhook")
    except Exception:  # background task: log, never crash the worker
        log.exception("review failed for %s#%s", repo, number)


@app.post("/api/webhooks/github")
async def github_webhook(request: Request, background: BackgroundTasks):
    body = await request.body()
    if not verify_signature(config.GITHUB_WEBHOOK_SECRET, body,
                            request.headers.get("X-Hub-Signature-256")):
        raise HTTPException(401, "Invalid webhook signature")
    event = request.headers.get("X-GitHub-Event", "")
    if event == "ping":
        return {"ok": True, "pong": True}
    if event != "pull_request":
        return {"ok": True, "ignored": event}
    try:
        payload = json.loads(body)
    except json.JSONDecodeError:
        raise HTTPException(400, "Malformed JSON")
    pr = payload.get("pull_request") or {}
    if payload.get("action") not in HANDLED_ACTIONS or pr.get("draft"):
        return {"ok": True, "ignored": payload.get("action")}
    repo = (payload.get("repository") or {}).get("full_name")
    number = pr.get("number")
    if not repo or not number:
        raise HTTPException(400, "Missing repository or PR number")
    background.add_task(_run_webhook_review, repo, number)
    return {"ok": True, "queued": f"{repo}#{number}"}


@app.get("/api/reviews")
def reviews(limit: int = 50):
    return db.list_reviews(min(max(limit, 1), 200))


@app.get("/api/reviews/{review_id}")
def review_detail(review_id: int):
    r = db.get_review(review_id)
    if not r:
        raise HTTPException(404, "Review not found")
    return r


@app.get("/api/stats")
def stats():
    return db.stats()
