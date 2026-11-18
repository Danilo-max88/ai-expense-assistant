from datetime import date

from sqlalchemy.orm import Session

from . import models, schemas


def create_expense(db: Session, expense: schemas.ExpenseCreate) -> models.Expense:
    db_expense = models.Expense(**expense.model_dump())
    db.add(db_expense)
    db.commit()
    db.refresh(db_expense)
    return db_expense


def get_expenses(
    db: Session,
    category: str | None = None,
    start_date: date | None = None,
    end_date: date | None = None,
) -> list[models.Expense]:
    query = db.query(models.Expense)
    if category:
        query = query.filter(models.Expense.category == category)
    if start_date:
        query = query.filter(models.Expense.date >= start_date)
    if end_date:
        query = query.filter(models.Expense.date <= end_date)
    return query.order_by(models.Expense.date.desc()).all()


def get_expense(db: Session, expense_id: int) -> models.Expense | None:
    return db.query(models.Expense).filter(models.Expense.id == expense_id).first()


def delete_expense(db: Session, expense_id: int) -> bool:
    expense = get_expense(db, expense_id)
    if not expense:
        return False
    db.delete(expense)
    db.commit()
    return True
