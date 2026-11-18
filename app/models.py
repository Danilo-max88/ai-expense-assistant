from sqlalchemy import Column, Date, DateTime, Float, Integer, String
from sqlalchemy.sql import func

from .database import Base


class Expense(Base):
    __tablename__ = "expenses"

    id = Column(Integer, primary_key=True, index=True)
    amount = Column(Float, nullable=False)
    category = Column(String, nullable=False, index=True)
    description = Column(String, nullable=False)
    date = Column(Date, nullable=False, index=True)
    created_at = Column(DateTime, server_default=func.now())
