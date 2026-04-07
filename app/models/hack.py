"""SQLAlchemy model for knowledge base 'hacks' (tips/articles).

Stores short articles users can read inside the app. Tags are persisted as a
comma-separated string for simplicity and converted to a list in the router
responses.
"""

from sqlalchemy import Column, Integer, String, Text, DateTime
from sqlalchemy.sql import func
from app.database import Base


class Hack(Base):
    __tablename__ = "hacks"

    # Surrogate integer primary key for easy pagination and lookups
    id = Column(Integer, primary_key=True, autoincrement=True)

    # Short title for the hack/article
    title = Column(String(200), nullable=False)

    # Main content (supports long text)
    content = Column(Text, nullable=False)

    # Optional small category label (e.g., productivity, wellness)
    category = Column(String(50), nullable=True)

    # Comma-separated tags for lightweight filtering ("focus,time")
    tags = Column(Text, nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    def __repr__(self) -> str:
        return f"<Hack(id={self.id}, title='{self.title}', category='{self.category}')>"
