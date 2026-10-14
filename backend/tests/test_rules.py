from app import config
from app.diff import parse_diff
from app.llm import FakeClient
from app.reviewer import review_diff
from app.rules import run_rules

EMPTY = {"summary": "s", "findings": []}


def _hits(src: str, path="a.py") -> list[str]:
    diff = f"diff --git a/{path} b/{path}\n--- a/{path}\n+++ b/{path}\n@@ -0,0 +1,1 @@\n+{src}\n"
    return [h["title"] for h in run_rules(parse_diff(diff)[0])]


def test_detects_common_problems():
    assert "Hardcoded secret" in _hits('API_KEY = "sk-live-123456789"')
    assert "Possible SQL injection" in _hits('q = "SELECT * FROM t WHERE id=" + uid')
    assert "Possible SQL injection" in _hits('q = f"DELETE FROM t WHERE id={uid}"')
    assert "Use of eval/exec" in _hits("x = eval(data)")
    assert "subprocess with shell=True" in _hits("subprocess.run(cmd, shell=True)")
    assert "TLS verification disabled" in _hits("requests.get(u, verify=False)")
    assert "Bare except" in _hits("except:")
    assert "AWS access key committed" in _hits("k = 'AKIAABCDEFGHIJKLMNOP'")


def test_clean_code_has_no_hits_and_language_scoping():
    assert _hits('q = "SELECT * FROM t WHERE id = %s"; cur.execute(q, (uid,))') == []
    assert _hits('password = os.environ["PASSWORD"]') == []
    assert "Use of eval/exec" not in _hits("x = eval(data)", path="notes.md")  # .py/.js only


def test_rules_merge_with_llm_without_duplicates(monkeypatch, sample_diff):
    monkeypatch.setattr(config, "ENABLE_RULES", True)
    r = review_diff(sample_diff, FakeClient(EMPTY))  # model finds nothing, rules still do
    titles = {f.title for f in r.findings}
    assert {"Possible SQL injection", "Hardcoded secret"} <= titles
    llm = {"summary": "s", "findings": [{"line": 11, "severity": "critical", "category": "security",
                                         "title": "SQL injection", "message": "model text"}]}
    r = review_diff(sample_diff, FakeClient(llm))
    on_11 = [f for f in r.findings if f.line == 11 and f.category == "security"]
    assert len(on_11) == 1 and on_11[0].message == "model text"  # LLM wins the duplicate


def test_rules_provider_needs_no_model(monkeypatch):
    from app.llm import RulesOnlyClient, get_client
    monkeypatch.setattr(config, "LLM_PROVIDER", "rules")
    assert isinstance(get_client(), RulesOnlyClient)
