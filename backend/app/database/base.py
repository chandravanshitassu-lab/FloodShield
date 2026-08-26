"""
Declarative base shared by all SQLAlchemy ORM models.
"""
import re
from sqlalchemy.orm import DeclarativeBase, declared_attr


class Base(DeclarativeBase):
    """Common declarative base for all ORM models."""

    @declared_attr.directive
    def __tablename__(cls) -> str:
        name = re.sub(r"(?<!^)(?=[A-Z])", "_", cls.__name__).lower()
        return name + "s"
