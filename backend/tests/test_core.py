import json

import pytest

from app.diff import parse_diff
from app.llm import FakeClient, LLMError
from app.reviewer import Finding, dedupe, parse_json, render_markdown, review_diff, score

GOOD = {
    "summary": "Adds a login query",
    "findings": [
        {"line": 11, "severity": "critical", "category": "security",
         "title": "SQL injection", "message": "String concat in query", "suggestion": "Use params"},
        {"line": 13, "severity": "high", "category": "security",
         "title": "Hardcoded secret", "message": "API key in source"},
    ],
}


def test_parse_diff_line_numbers(sample_diff):
    files = parse_diff(sample_diff)
    assert [f.path for f in files] == ["app/auth.py", "package-lock.json"]
    auth = files[0]
    assert sorted(auth.added_lines) == [11, 12, 13]
    assert 10 in auth.visible_lines  # context line
    assert auth.reviewable and not files[1].reviewable  # lockfile skipped


def test_parse_json_tolerates_fences_and_prose():
    assert parse_json('```json\n{"a": 1}\n```') == {"a": 1}
    assert parse_json('Sure! Here you go: {"a": 2} hope it helps') == {"a": 2}
    with pytest.raises(json.JSONDecodeError):
        parse_json("no json here")


def test_review_diff_filters_and_sorts(sample_diff):
    llm = FakeClient(GOOD)
    r = review_diff(sample_diff, llm)
    assert r.files_reviewed == 1 and r.files_skipped == 1
    assert [f.severity for f in r.findings] == ["critical", "high"]
    assert r.score == 100 - 25 - 14
    assert len(llm.calls) == 1  # lockfile never sent to the model


def test_line_outside_diff_is_snapped_to_nearest_added_line(sample_diff):
    bad = {"summary": "x", "findings": [
        {"line": 999, "severity": "high", "category": "bug", "title": "T", "message": "m"}]}
    r = review_diff(sample_diff, FakeClient(bad))
    assert r.findings[0].line == 13  # closest added line


def test_unknown_severity_and_category_are_normalised(sample_diff):
    odd = {"summary": "x", "findings": [
        {"line": 11, "severity": "SCARY", "category": "vibes", "title": "T", "message": "m"}]}
    f = review_diff(sample_diff, FakeClient(odd)).findings[0]
    assert (f.severity, f.category) == ("low", "maintainability")


def test_min_severity_filter(sample_diff):
    r = review_diff(sample_diff, FakeClient(GOOD), min_severity="critical")
    assert len(r.findings) == 1


def test_retry_on_bad_json_then_success(sample_diff):
    llm = FakeClient(["not json at all", GOOD])
    assert len(review_diff(sample_diff, llm).findings) == 2
    assert len(llm.calls) == 2


def test_persistent_bad_json_raises(sample_diff):
    with pytest.raises(LLMError):
        review_diff(sample_diff, FakeClient("garbage"))


def test_dedupe_and_score():
    a = Finding("f.py", 1, "high", "bug", "Same", "m")
    assert len(dedupe([a, Finding("f.py", 1, "high", "bug", "same", "m2")])) == 1
    assert score([]) == 100
    assert score([Finding("f", 1, "critical", "bug", "t", "m")] * 5) == 0


def test_markdown_render(sample_diff):
    md = render_markdown(review_diff(sample_diff, FakeClient(GOOD)))
    assert "SQL injection" in md and "score **61/100**" in md
