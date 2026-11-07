from sqlalchemy import Column, Integer, String, Text

from app.database import Base


class Regulation(Base):
    __tablename__ = "regulations"

    id = Column(Integer, primary_key=True, autoincrement=True)
    code = Column(String(50), nullable=False, unique=True)
    name = Column(String(255))
    description = Column(Text)
    sort_order = Column(Integer, default=0)


class Region(Base):
    __tablename__ = "regions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    category = Column(String(50))
    db_files = Column(Text)


class CostFormula(Base):
    __tablename__ = "cost_formula"

    id = Column(Integer, primary_key=True)
    formula_id = Column(Integer, nullable=False)
    name = Column(String(255))
    description = Column(String(255))
