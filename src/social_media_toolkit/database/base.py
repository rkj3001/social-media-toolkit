"""SQLAlchemy declarative base shared by all applications."""

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass

