from python_validation.escalation_checker import independent_escalation_check, keyword_escalation_hit
from python_validation.hallucination_checker import find_unsupported_promises
from complaint_processing.preprocessing import is_near_duplicate, fingerprint


def test_keyword_escalation_hit_detects_safety_language():
    assert keyword_escalation_hit("I smell burning, this feels dangerous") is not None


def test_keyword_escalation_hit_none_for_benign_text():
    assert keyword_escalation_hit("My order arrived a day late") is None


def test_independent_escalation_check_rule_mandate():
    should_escalate, reason = independent_escalation_check("normal text", rule_must_escalate=True)
    assert should_escalate is True
    assert "Rule matrix" in reason


def test_independent_escalation_check_repeat_count():
    should_escalate, _ = independent_escalation_check("normal text", rule_must_escalate=False, repeat_count=3)
    assert should_escalate is True


def test_unsupported_promise_flagged_when_absent_from_policy():
    flags = find_unsupported_promises("We guarantee a $200 refund within 24 hours.", ["Standard refund window is 5-7 business days."])
    assert any("guarantee" in f.lower() for f in flags)


def test_near_duplicate_detection():
    a = "My package never arrived even though tracking says delivered"
    b = "My package never arrived, tracking says delivered but nothing here"
    assert is_near_duplicate(a, b, threshold=0.5) is True


def test_fingerprint_is_deterministic():
    assert fingerprint("a@b.com", "hello world") == fingerprint("a@b.com", "hello world")
