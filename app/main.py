from datetime import date, timedelta

from fastapi import Depends, FastAPI, HTTPException, Query
from sqlalchemy.orm import Session

from . import claude_service, crud, models, schemas
from .database import engine, get_db

models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="AI Expense Assistant", version="0.1.0")


@app.post("/expenses", response_model=schemas.ExpenseOut, status_code=201)
def create_expense(expense: schemas.ExpenseCreate, db: Session = Depends(get_db)):
    return crud.create_expense(db, expense)


@app.post("/expenses/parse", response_model=schemas.ExpenseOut, status_code=201)
def parse_and_create_expense(
    request: schemas.ParseTextRequest, db: Session = Depends(get_db)
):
    parsed = claude_service.parse_expense_text(request.text)
    expense = schemas.ExpenseCreate(**parsed)
    return crud.create_expense(db, expense)


@app.get("/expenses", response_model=list[schemas.ExpenseOut])
def list_expenses(
    category: str | None = None,
    start_date: date | None = None,
    end_date: date | None = None,
    db: Session = Depends(get_db),
):
    return crud.get_expenses(db, category=category, start_date=start_date, end_date=end_date)


@app.delete("/expenses/{expense_id}", status_code=204)
def delete_expense(expense_id: int, db: Session = Depends(get_db)):
    if not crud.delete_expense(db, expense_id):
        raise HTTPException(status_code=404, detail="Expense not found")


@app.get("/expenses/summary", response_model=schemas.SummaryResponse)
def expense_summary(
    period: str = Query("week", pattern="^(week|month)$"),
    db: Session = Depends(get_db),
):
    end_date = date.today()
    start_date = end_date - timedelta(days=7 if period == "week" else 30)
    expenses = crud.get_expenses(db, start_date=start_date, end_date=end_date)

    total = sum(e.amount for e in expenses)
    by_category: dict[str, float] = {}
    for e in expenses:
        by_category[e.category] = by_category.get(e.category, 0) + e.amount

    expense_dicts = [
        {
            "date": e.date.isoformat(),
            "amount": e.amount,
            "category": e.category,
            "description": e.description,
        }
        for e in expenses
    ]
    insight = claude_service.generate_spending_summary(expense_dicts, period)

    return schemas.SummaryResponse(
        period_label=period, total=total, by_category=by_category, insight=insight
    )
