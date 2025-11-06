from sqlalchemy.orm import declarative_base
from sqlalchemy import Column, Integer, String, Numeric
from decimal import Decimal

Base = declarative_base()

class Account(Base):
    __tablename__ = "accounts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(300), nullable=False)
    number = Column(String(100), unique=True, nullable=False, index=True)
    balance = Column(Numeric(18, 4), nullable=False, default=0)

    def to_dict(self) -> dict:
        return {
            "id": int(self.id),
            "name": self.name,
            "number": self.number,
            "balance": float(self.balance),
        }
