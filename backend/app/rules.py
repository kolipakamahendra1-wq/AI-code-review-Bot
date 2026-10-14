"""Deterministic security/bug rules run on added lines before (and alongside) the LLM.
They are instant, free and never hallucinate, so obvious problems are always caught
even when a small local model misses them."""
import re
from dataclasses import dataclass

from .diff import FileDiff


@dataclass(frozen=True)
class Rule:
    id: str
    pattern: re.Pattern
    severity: str
    category: str
    title: str
    message: str
    suggestion: str
    exts: tuple[str, ...] = ()  # empty = all files


def _r(rid, pat, sev, cat, title, msg, fix, exts=()):
    return Rule(rid, re.compile(pat, re.I), sev, cat, title, msg, fix, exts)


PY = (".py",)
JS = (".js", ".jsx", ".ts", ".tsx", ".mjs")

RULES = [
    _r("secret", r"""(api[_-]?key|secret|passwd|password|token|private[_-]?key)\w*\s*[:=]\s*["'][^"'\s]{8,}["']""",
       "high", "security", "Hardcoded secret",
       "A credential appears to be committed in source. Anyone with repo access (or its history) can use it.",
       "Load it from an environment variable or a secret manager and rotate the leaked value."),
    _r("aws-key", r"AKIA[0-9A-Z]{16}", "critical", "security", "AWS access key committed",
       "This looks like an AWS access key ID.", "Revoke the key immediately and use IAM roles or env vars."),
    _r("private-key", r"-----BEGIN (RSA |EC |OPENSSH )?PRIVATE KEY-----", "critical", "security",
       "Private key committed", "A private key must never live in the repository.",
       "Remove it, rotate the key, and purge it from git history."),
    _r("sql-concat", r"""(select|insert|update|delete)\b[^\n]{0,80}["']\s*(\+|%|\.format|,)|f["'](select|insert|update|delete)\b[^\n]*\{""",
       "high", "security", "Possible SQL injection",
       "A SQL statement is built with string concatenation/formatting from variables.",
       "Use parameterised queries (e.g. cursor.execute(sql, params))."),
    _r("eval", r"\b(eval|exec)\s*\(", "high", "security", "Use of eval/exec",
       "Executing dynamic strings can lead to remote code execution.",
       "Use ast.literal_eval / json.loads or an explicit dispatch table.", PY + JS),
    _r("shell-true", r"shell\s*=\s*True", "high", "security", "subprocess with shell=True",
       "Passing a string to the shell enables command injection.",
       "Pass an argument list and drop shell=True.", PY),
    _r("tls-off", r"verify\s*=\s*False|rejectUnauthorized\s*:\s*false", "high", "security",
       "TLS verification disabled", "Disabling certificate checks allows man-in-the-middle attacks.",
       "Keep verification on; pin a CA bundle if you use a private CA."),
    _r("pickle", r"\bpickle\.loads?\(|yaml\.load\((?![^)]*Loader)", "medium", "security",
       "Unsafe deserialisation", "Deserialising untrusted data can execute arbitrary code.",
       "Use json, or yaml.safe_load.", PY),
    _r("bare-except", r"^\s*except\s*:\s*(#.*)?$", "medium", "bug", "Bare except",
       "A bare except also swallows KeyboardInterrupt/SystemExit and hides real errors.",
       "Catch specific exceptions (except ValueError:) and log them.", PY),
    _r("inner-html", r"innerHTML\s*=|dangerouslySetInnerHTML", "medium", "security",
       "Raw HTML injection", "Writing unsanitised strings into the DOM enables XSS.",
       "Use textContent / React escaping, or sanitise with DOMPurify.", JS),
    _r("debug-left", r"\bbreakpoint\(\)|\bpdb\.set_trace\(\)|\bdebugger;|console\.log\(", "low",
       "maintainability", "Debug statement left in code",
       "Debug leftovers add noise and can leak data in production.", "Remove it or use a logger."),
    _r("todo", r"\b(TODO|FIXME|HACK)\b", "info", "maintainability", "Unresolved TODO",
       "A TODO was added in this change.", "Track it in an issue or resolve it before merging."),
]


def run_rules(fd: FileDiff) -> list[dict]:
    out = []
    for ln, text in fd.added_lines.items():
        for rule in RULES:
            if rule.exts and not fd.path.endswith(rule.exts):
                continue
            if rule.pattern.search(text):
                out.append({"line": ln, "severity": rule.severity, "category": rule.category,
                            "title": rule.title, "message": rule.message, "suggestion": rule.suggestion})
    return out
