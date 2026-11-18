import os
from datetime import date
from functools import lru_cache

import anthropic

MODEL = os.getenv("ANTHROPIC_MODEL", "claude-opus-4-8")

VALID_CATEGORIES = [
    "food",
    "transport",
    "housing",
    "entertainment",
    "health",
    "shopping",
    "other",
]


@lru_cache
def get_client() -> anthropic.Anthropic:
    return anthropic.Anthropic()


def parse_expense_text(text: str, today: date | None = None) -> dict:
    """Extract structured expense data from free-form text using forced tool use."""
    today = today or date.today()
    client = get_client()

    response = client.messages.create(
        model=MODEL,
        max_tokens=1024,
        tools=[
            {
                "name": "record_expense",
                "description": "Record a single parsed expense extracted from the user's free-form text.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "amount": {
                            "type": "number",
                            "description": "Expense amount as a positive number.",
                        },
                        "category": {
                            "type": "string",
                            "enum": VALID_CATEGORIES,
                        },
                        "description": {
                            "type": "string",
                            "description": "Short description of what was purchased.",
                        },
                        "date": {
                            "type": "string",
                            "description": "ISO date (YYYY-MM-DD) the expense occurred on.",
                        },
                    },
                    "required": ["amount", "category", "description", "date"],
                },
            }
        ],
        tool_choice={"type": "tool", "name": "record_expense"},
        messages=[
            {
                "role": "user",
                "content": (
                    f"Today's date is {today.isoformat()}. "
                    f'Extract the expense from this text: "{text}"'
                ),
            }
        ],
    )

    tool_use = next(block for block in response.content if block.type == "tool_use")
    return tool_use.input


def generate_spending_summary(expenses: list[dict], period_label: str) -> str:
    """Generate a short natural-language insight about a set of expenses."""
    if not expenses:
        return f"No expenses recorded for this {period_label}."

    client = get_client()
    lines = "\n".join(
        f"- {e['date']}: {e['amount']} ({e['category']}) - {e['description']}"
        for e in expenses
    )
    prompt = (
        f"Here are the expenses for this {period_label}:\n{lines}\n\n"
        "Write a short (3-4 sentence) insight about this spending: the biggest "
        "category, anything unusual, and one practical tip. Be direct and specific."
    )

    response = client.messages.create(
        model=MODEL,
        max_tokens=512,
        messages=[{"role": "user", "content": prompt}],
    )

    return next(block.text for block in response.content if block.type == "text")
