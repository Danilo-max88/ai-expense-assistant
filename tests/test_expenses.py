def test_create_expense(client):
    response = client.post(
        "/expenses",
        json={
            "amount": 1500,
            "category": "food",
            "description": "Grocery shopping",
            "date": "2026-11-15",
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["amount"] == 1500
    assert data["category"] == "food"
    assert "id" in data


def test_create_expense_rejects_non_positive_amount(client):
    response = client.post(
        "/expenses",
        json={
            "amount": 0,
            "category": "food",
            "description": "Invalid",
            "date": "2026-11-15",
        },
    )
    assert response.status_code == 422


def test_list_expenses_empty(client):
    response = client.get("/expenses")
    assert response.status_code == 200
    assert response.json() == []


def test_list_expenses_after_create(client):
    client.post(
        "/expenses",
        json={
            "amount": 500,
            "category": "transport",
            "description": "Bus ticket",
            "date": "2026-11-10",
        },
    )
    response = client.get("/expenses")
    assert response.status_code == 200
    assert len(response.json()) == 1


def test_list_expenses_filters_by_category(client):
    client.post(
        "/expenses",
        json={"amount": 100, "category": "food", "description": "Lunch", "date": "2026-11-10"},
    )
    client.post(
        "/expenses",
        json={"amount": 50, "category": "transport", "description": "Taxi", "date": "2026-11-10"},
    )
    response = client.get("/expenses", params={"category": "food"})
    data = response.json()
    assert len(data) == 1
    assert data[0]["category"] == "food"


def test_delete_expense(client):
    create_resp = client.post(
        "/expenses",
        json={"amount": 200, "category": "other", "description": "Misc", "date": "2026-11-01"},
    )
    expense_id = create_resp.json()["id"]

    delete_resp = client.delete(f"/expenses/{expense_id}")
    assert delete_resp.status_code == 204
    assert client.get("/expenses").json() == []


def test_delete_nonexistent_expense(client):
    response = client.delete("/expenses/9999")
    assert response.status_code == 404


def test_parse_expense_calls_claude(client, monkeypatch):
    def fake_parse(text, today=None):
        return {
            "amount": 1200,
            "category": "food",
            "description": "Coffee",
            "date": "2026-11-17",
        }

    monkeypatch.setattr("app.main.claude_service.parse_expense_text", fake_parse)

    response = client.post("/expenses/parse", json={"text": "spent 1200 on coffee yesterday"})
    assert response.status_code == 201
    data = response.json()
    assert data["amount"] == 1200
    assert data["category"] == "food"


def test_summary_with_no_expenses(client, monkeypatch):
    monkeypatch.setattr(
        "app.main.claude_service.generate_spending_summary",
        lambda expenses, period_label: f"No expenses recorded for this {period_label}.",
    )

    response = client.get("/expenses/summary", params={"period": "week"})
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 0
    assert data["by_category"] == {}
