"""CLI used by the GitHub Action:  python -m app.cli review --repo o/r --pr 12

Exits non-zero when findings at/above --fail-on exist, so it can gate CI."""
import argparse
import json
import os
import sys

from . import config
from .github import GitHubClient
from .llm import LLMError, get_client
from .pipeline import review_pull_request
from .reviewer import SEVERITIES


def _pr_from_event() -> tuple[str | None, int | None]:
    path = os.getenv("GITHUB_EVENT_PATH")
    if not path or not os.path.exists(path):
        return None, None
    with open(path, encoding="utf-8") as f:
        ev = json.load(f)
    pr = ev.get("pull_request") or {}
    return os.getenv("GITHUB_REPOSITORY"), pr.get("number")


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="pr-sentinel")
    sub = p.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("review", help="review a pull request")
    r.add_argument("--repo")
    r.add_argument("--pr", type=int)
    r.add_argument("--no-post", action="store_true", help="print only, don't comment")
    r.add_argument("--fail-on", choices=SEVERITIES, help="exit 1 if a finding >= this severity")
    r.add_argument("--db", default=os.getenv("DB_PATH", "data/reviews.db"))
    args = p.parse_args(argv)

    config.DB_PATH = args.db
    ev_repo, ev_pr = _pr_from_event()
    repo, number = args.repo or ev_repo, args.pr or ev_pr
    if not repo or not number:
        p.error("need --repo and --pr (or run inside a pull_request workflow)")
    try:
        res = review_pull_request(repo, number, get_client(), GitHubClient(),
                                  post=not args.no_post, source="action", force=True)
    except (LLMError, Exception) as e:  # noqa: BLE001 - CLI boundary
        print(f"error: {e}", file=sys.stderr)
        return 2
    print(f"score {res['score']}/100 - {len(res['findings'])} finding(s) - model {res['model']}")
    for f in res["findings"]:
        print(f"  [{f['severity']}] {f['file']}:{f['line']}  {f['title']}")
    if args.fail_on:
        floor = SEVERITIES.index(args.fail_on)
        if any(SEVERITIES.index(f["severity"]) >= floor for f in res["findings"]):
            return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
