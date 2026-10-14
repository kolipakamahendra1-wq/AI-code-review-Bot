"""End-to-end PR review: fetch -> review -> post -> persist. Shared by the
webhook, the manual endpoint and the CLI/GitHub Action."""
from . import db
from .github import GitHubClient
from .llm import LLMClient
from .reviewer import render_comment, render_markdown, review_diff


def review_pull_request(repo: str, number: int, llm: LLMClient, gh: GitHubClient | None = None,
                        *, post: bool = True, source: str = "manual", force: bool = False) -> dict:
    gh = gh or GitHubClient()
    pr = gh.get_pr(repo, number)
    sha = pr["head"]["sha"]
    title = pr.get("title", "")
    if not force and db.already_reviewed(repo, number, sha):
        return {"skipped": True, "reason": "already reviewed this commit", "head_sha": sha}
    try:
        result = review_diff(gh.get_diff(repo, number), llm)
        data = result.as_dict()
        if post:
            comments = [
                {"path": f.file, "line": f.line, "side": "RIGHT", "body": render_comment(f)}
                for f in result.findings
            ]
            gh.post_review(repo, number, sha, render_markdown(result), comments)
        rid = db.save_review(data, source=source, repo=repo, pr_number=number,
                             head_sha=sha, title=title)
    except Exception as e:
        db.save_review({}, source=source, repo=repo, pr_number=number, head_sha=sha,
                       title=title, status="error", error=str(e)[:500])
        raise
    return {"skipped": False, "review_id": rid, "head_sha": sha, **data}
