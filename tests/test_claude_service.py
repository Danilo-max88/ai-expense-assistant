from datetime import date
from unittest.mock import MagicMock, patch

from app import claude_service


def _tool_use_response(input_data):
    block = MagicMock()
    block.type = "tool_use"
    block.input = input_data
    response = MagicMock()
    response.content = [block]
    return response


def _text_response(text):
    block = MagicMock()
    block.type = "text"
    block.text = text
    response = MagicMock()
    response.content = [block]
    return response


def test_parse_expense_text_returns_tool_input():
    expected = {
        "amount": 1500.0,
        "category": "food",
        "description": "Coffee",
        "date": "2026-11-17",
    }
    fake_client = MagicMock()
    fake_client.messages.create.return_value = _tool_use_response(expected)

    with patch.object(claude_service, "get_client", return_value=fake_client):
        result = claude_service.parse_expense_text(
            "spent 1500 on coffee", today=date(2026, 11, 17)
        )

    assert result == expected
    fake_client.messages.create.assert_called_once()
    call_kwargs = fake_client.messages.create.call_args.kwargs
    assert call_kwargs["tool_choice"] == {"type": "tool", "name": "record_expense"}
    assert "2026-11-17" in call_kwargs["messages"][0]["content"]


def test_generate_spending_summary_empty_list_skips_api_call():
    fake_client = MagicMock()

    with patch.object(claude_service, "get_client", return_value=fake_client):
        result = claude_service.generate_spending_summary([], "week")

    assert "no expenses" in result.lower()
    fake_client.messages.create.assert_not_called()


def test_generate_spending_summary_calls_claude():
    fake_client = MagicMock()
    fake_client.messages.create.return_value = _text_response(
        "You spent most on food this week."
    )

    with patch.object(claude_service, "get_client", return_value=fake_client):
        result = claude_service.generate_spending_summary(
            [{"date": "2026-11-17", "amount": 1500, "category": "food", "description": "Coffee"}],
            "week",
        )

    assert result == "You spent most on food this week."
