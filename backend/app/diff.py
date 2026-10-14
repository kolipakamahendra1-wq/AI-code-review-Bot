"""Unified-diff parser. Tracks which new-file lines are visible in the diff so
inline review comments only land on lines GitHub will accept."""
import re
from dataclasses import dataclass, field

HUNK_RE = re.compile(r"^@@ -\d+(?:,\d+)? \+(\d+)(?:,\d+)? @@")
SKIP_NAMES = {
    "package-lock.json", "yarn.lock", "pnpm-lock.yaml", "poetry.lock",
    "Pipfile.lock", "Cargo.lock", "go.sum", "composer.lock",
}
SKIP_SUFFIXES = (
    ".min.js", ".min.css", ".map", ".svg", ".png", ".jpg", ".jpeg", ".gif",
    ".ico", ".pdf", ".woff", ".woff2", ".lock",
)


@dataclass
class FileDiff:
    path: str
    status: str = "modified"  # added | deleted | modified
    added_lines: dict[int, str] = field(default_factory=dict)  # new line no -> text
    visible_lines: set[int] = field(default_factory=set)       # added + context
    numbered: list[str] = field(default_factory=list)          # prompt-ready lines
    binary: bool = False

    @property
    def reviewable(self) -> bool:
        name = self.path.rsplit("/", 1)[-1]
        return (
            not self.binary
            and self.status != "deleted"
            and bool(self.added_lines)
            and name not in SKIP_NAMES
            and not self.path.endswith(SKIP_SUFFIXES)
        )


def parse_diff(text: str) -> list[FileDiff]:
    files: list[FileDiff] = []
    cur: FileDiff | None = None
    new_ln = 0
    in_hunk = False
    for raw in text.splitlines():
        if raw.startswith("diff --git "):
            m = re.match(r"diff --git a/(.*?) b/(.*)$", raw)
            cur = FileDiff(path=m.group(2) if m else raw[11:])
            files.append(cur)
            in_hunk = False
            continue
        if cur is None:
            continue
        if not in_hunk:
            if raw.startswith("new file mode"):
                cur.status = "added"
            elif raw.startswith("deleted file mode"):
                cur.status = "deleted"
            elif raw.startswith("Binary files") or raw.startswith("GIT binary patch"):
                cur.binary = True
            elif raw.startswith("+++ "):
                p = raw[4:].strip()
                if p != "/dev/null":
                    cur.path = p[2:] if p.startswith("b/") else p
        m = HUNK_RE.match(raw)
        if m:
            new_ln = int(m.group(1))
            in_hunk = True
            cur.numbered.append(raw)
            continue
        if not in_hunk:
            continue
        if raw.startswith("+"):
            cur.added_lines[new_ln] = raw[1:]
            cur.visible_lines.add(new_ln)
            cur.numbered.append(f"{new_ln}: +{raw[1:]}")
            new_ln += 1
        elif raw.startswith("-"):
            cur.numbered.append(f"   -{raw[1:]}")
        elif raw.startswith("\\"):
            continue
        else:
            cur.visible_lines.add(new_ln)
            cur.numbered.append(f"{new_ln}:  {raw[1:] if raw.startswith(' ') else raw}")
            new_ln += 1
    return files
