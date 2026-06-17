"""Tests for fingerprint + normalize_message."""
from fingerprint import (
    compute_fingerprint,
    compute_fingerprint_loose,
    line_bucket,
    normalize_message,
)


def test_line_bucket_collapses_5_line_window():
    assert line_bucket(40) == 8
    assert line_bucket(44) == 8
    assert line_bucket(45) == 9


def test_normalize_message_lowercases_and_strips():
    assert normalize_message("  Function MISSING return  ") == "function missing return"


def test_normalize_message_replaces_numbers():
    assert normalize_message("12 errors in foo") == "N errors in foo"


def test_normalize_message_replaces_paths():
    assert normalize_message("error in src/foo/bar.py: bad") == "error in <path>: bad"


def test_normalize_message_replaces_hex_ids():
    assert "<id>" in normalize_message("commit abc1234def deadbeefcafe found")


def test_fingerprint_is_stable_across_line_shift():
    a = compute_fingerprint("03-mypy", "src/foo.py", 42, "missing return")
    b = compute_fingerprint("03-mypy", "src/foo.py", 44, "missing return")
    assert a == b   # both fall into line_bucket 8


def test_fingerprint_changes_with_check_id():
    a = compute_fingerprint("03-mypy", "src/foo.py", 42, "msg")
    b = compute_fingerprint("01-ruff-check", "src/foo.py", 42, "msg")
    assert a != b


def test_fingerprint_loose_ignores_file_within_module():
    a = compute_fingerprint_loose("03-mypy", "src/processor/m2.py", "missing return")
    b = compute_fingerprint_loose("03-mypy", "src/processor/m3.py", "missing return")
    assert a == b   # same top-level module 'processor'


def test_fingerprint_loose_differs_across_modules():
    a = compute_fingerprint_loose("03-mypy", "src/processor/m2.py", "msg")
    b = compute_fingerprint_loose("03-mypy", "src/ingestor/parse.py", "msg")
    assert a != b
