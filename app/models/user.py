from sqlalchemy import Column, String, DateTime, JSON, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base
import uuid

def gen_uuid():
    return str(uuid.uuid4())

class User(Base):
    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    username = Column(String(80), unique=True, nullable=False)  # email or phone (normalized)
    password_hash = Column(Text, nullable=False)                # bcrypt hash
    avatar = Column(Text, nullable=True)                        # URL
    preferences = Column(JSON, nullable=False, default=dict)    # Free-form
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    moods = relationship("Mood", back_populates="user", cascade="all, delete-orphan")
    tasks = relationship("Task", back_populates="user", cascade="all, delete-orphan")
