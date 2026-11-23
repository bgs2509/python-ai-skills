from src.buggy_module import classify_priority, dedupe_emails


def test_dedupe_basic():
    assert dedupe_emails(["A@x.com", "a@x.com ", "b@x.com"]) == ["a@x.com", "b@x.com"]


def test_classify_low():
    assert classify_priority(10) == "low"


def test_classify_high():
    assert classify_priority(75) == "high"
