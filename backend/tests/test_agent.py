from __future__ import annotations

from unittest.mock import patch
import pytest

from app.agent.tools import calculator, current_date, dispatch_tool


class TestCalculator:
    def test_basic_arithmetic(self):
        assert calculator("10 + 5") == "15"
        assert calculator("7 * 8") == "56"
        assert calculator("100 / 4") == "25"
        assert calculator("2 ** 8") == "256"

    def test_expression_precedence(self):
        assert calculator("(2 + 3) * 4") == "20"

    def test_division_by_zero(self):
        res = calculator("5 / 0")
        assert "zero" in res.lower()

    def test_rejects_code_injection(self):
        res = calculator("__import__('os').system('ls')")
        assert "Error" in res or "Unsupported" in res


def test_date_tool():
    date_str = current_date()
    assert "Today is" in date_str
    assert "UTC" in date_str


def test_agent_direct_execution():
    with patch("app.agent.state_machine.classify_intent", return_value=("direct", None)), \
         patch("app.agent.state_machine.llm") as mock_llm:
        mock_llm.generate.return_value = ("General knowledge response.", 42)
        from app.agent.state_machine import run
        result = run("Hello! Who are you?")

    assert result.intent == "direct"
    assert "General knowledge" in result.answer


def test_agent_tool_execution():
    with patch("app.agent.state_machine.classify_intent", return_value=("tool", "calculator")):
        from app.agent.state_machine import run
        result = run("Calculate 50 * 20")

    assert result.intent == "tool"
    assert "1000" in result.answer
