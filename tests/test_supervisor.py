"""Tests for supervisor gate."""

from oneshot.supervisor import gate_passed


def test_gate_passed_with_passing_result():
    state = {
        "gate_results": [{"stage": "test", "passed": True, "score": 0.9}]
    }
    assert gate_passed(state) == "pass"


def test_gate_passed_with_failing_result():
    state = {
        "gate_results": [{"stage": "test", "passed": False, "score": 0.5}]
    }
    assert gate_passed(state) == "retry"


def test_gate_passed_empty_results():
    state = {"gate_results": []}
    assert gate_passed(state) == "retry"


def test_gate_passed_uses_latest():
    state = {
        "gate_results": [
            {"stage": "test", "passed": False, "score": 0.3},
            {"stage": "test", "passed": True, "score": 0.9},
        ]
    }
    assert gate_passed(state) == "pass"
