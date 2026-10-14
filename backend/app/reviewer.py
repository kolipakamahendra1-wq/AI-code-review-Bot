"""Review engine: diff -> per-file LLM review -> validated, deduped findings."""
import json
import re
from dataclasses import asdict, dataclass

from . import config
from .diff import FileDiff, parse_diff
from .llm import LLMClient, LLMError
from .rules import run_rules

SEVERITIES = ["info", "low", "medium", "high", "critical"]
CATEGORIES = {"bug", "security", "performance", "style", "test", "maintainability"}
PENALTY = {"info": 0, "low": 2, "medium": 6, "high": 14, "critical": 25}

SYSTEM = """You are a senior engineer doing a pull-request code review.
Review ONLY the changed lines (lines marked with +). Report real problems:
bugs, security vulnerabilities (injection, hardcoded secrets, unsafe eval, missing auth),
performance issues, missing error handling, and missing tests. Do NOT nitpick formatting.
Each diff line is prefixed with its line number in the new file, like "12: +code".
Respond with JSON only, exactly this shape:
{"summary": "one sentence about this file's change",
 "findings": [{"line": 12, "severity": "info|low|medium|high|critical",
 "category": "bug|security|performance|style|test|maintainability",
 "title": "short title", "message": "what is wrong and why it matters",
 "suggestion": "concrete fix, optionally a code snippet"}]}
The line must be a line number taken from the diff.
If the code is fine return {"summary": "...", "findings": []}."""


@dataclass
class Finding:
    file: str
    line: int
    severity: str
    category: str
    title: str
    message: str
    suggestion: str = ""

    def as_dict(self) -> dict:
        return asdict(self)


@dataclass
class ReviewResult:
    summary: str
    score: int
    findings: list[Finding]
    files_reviewed: int
    files_skipped: int
    model: str

    def as_dict(self) -> dict:
        d = asdict(self)
        d["findings"] = [f.as_dict() for f in self.findings]
        return d


def parse_json(text: str) -> dict:
    """Tolerant JSON extraction: handles code fences and surrounding prose."""
    text = text.strip()
    text = re.sub(r"^```(?:json)?\s*|\s*```$", "", text)
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        m = re.search(r"\{.*\}", text, re.DOTALL)
        if m:
            return json.loads(m.group(0))
        raise


def _clean(raw: dict, fd: FileDiff) -> Finding | None:
    try:
        line = int(raw.get("line"))
    except (TypeError, ValueError):
        return None
    if line not in fd.visible_lines:  # GitHub rejects comments outside the diff
        if not fd.added_lines:
            return None
        line = min(fd.added_lines, key=lambda n: abs(n - line))
    sev = str(raw.get("severity", "low")).lower()
    sev = sev if sev in SEVERITIES else "low"
    cat = str(raw.get("category", "bug")).lower()
    cat = cat if cat in CATEGORIES else "maintainability"
    title = str(raw.get("title", "")).strip()[:120]
    msg = str(raw.get("message", "")).strip()
    if not title and not msg:
        return None
    return Finding(fd.path, line, sev, cat, title or msg[:60], msg, str(raw.get("suggestion", "")).strip())


def _review_file(fd: FileDiff, llm: LLMClient) -> tuple[str, list[Finding]]:
    body = "\n".join(fd.numbered)[: config.MAX_DIFF_CHARS]
    user = f"File: {fd.path}\n\n{body}"
    last_err: Exception | None = None
    data = None
    for _ in range(2):  # one retry on malformed JSON
        out = llm.complete(SYSTEM, user)
        try:
            data = parse_json(out)
            if isinstance(data, dict):
                break
            last_err = ValueError("not a JSON object")
        except (json.JSONDecodeError, TypeError) as e:
            last_err = e
        data = None
    if data is None:
        raise LLMError(f"Model returned invalid JSON for {fd.path}: {last_err}")
    findings = []
    for raw in data.get("findings") or []:
        if isinstance(raw, dict):
            f = _clean(raw, fd)
            if f:
                findings.append(f)
    return str(data.get("summary", "")).strip(), findings


def dedupe(findings: list[Finding]) -> list[Finding]:
    seen, out = set(), []
    for f in findings:
        key = (f.file, f.line, f.category)  # one finding per category per line; first (LLM) wins
        if key not in seen:
            seen.add(key)
            out.append(f)
    return out


def score(findings: list[Finding]) -> int:
    return max(0, 100 - sum(PENALTY[f.severity] for f in findings))


def review_diff(diff_text: str, llm: LLMClient, min_severity: str = "low",
                use_rules: bool | None = None) -> ReviewResult:
    use_rules = config.ENABLE_RULES if use_rules is None else use_rules
    files = parse_diff(diff_text)
    todo = [f for f in files if f.reviewable][: config.MAX_FILES]
    skipped = len(files) - len(todo)
    findings: list[Finding] = []
    summaries: list[str] = []
    for fd in todo:
        s, fs = _review_file(fd, llm)
        if s:
            summaries.append(f"`{fd.path}`: {s}")
        findings.extend(fs)
        if use_rules:  # after the LLM so its richer explanation wins on duplicates
            findings.extend(f for f in (_clean(r, fd) for r in run_rules(fd)) if f)
    floor = SEVERITIES.index(min_severity if min_severity in SEVERITIES else "low")
    findings = [f for f in dedupe(findings) if SEVERITIES.index(f.severity) >= floor]
    findings.sort(key=lambda f: (-SEVERITIES.index(f.severity), f.file, f.line))
    return ReviewResult(
        "\n".join(summaries) or "No reviewable changes.",
        score(findings), findings, len(todo), skipped, llm.name,
    )


ICON = {"critical": "🔴", "high": "🟠", "medium": "🟡", "low": "🔵", "info": "⚪"}


def render_markdown(r: ReviewResult) -> str:
    counts = {s: sum(1 for f in r.findings if f.severity == s) for s in reversed(SEVERITIES)}
    badge = " · ".join(f"{ICON[s]} {n} {s}" for s, n in counts.items() if n) or "✅ no issues found"
    lines = [f"## 🤖 AI Code Review — score **{r.score}/100**", "", badge, "", r.summary, ""]
    if r.findings:
        lines += ["| Sev | File | Line | Issue |", "|---|---|---|---|"]
        for f in r.findings:
            lines.append(f"| {ICON[f.severity]} {f.severity} | `{f.file}` | {f.line} | {f.title} |")
    lines += ["", f"<sub>Reviewed {r.files_reviewed} file(s) with `{r.model}`</sub>"]
    return "\n".join(lines)


def render_comment(f: Finding) -> str:
    body = f"**{f.severity.upper()} · {f.category}** — {f.title}\n\n{f.message}"
    if f.suggestion:
        body += f"\n\n💡 **Suggestion:** {f.suggestion}"
    return body
