from . import db
from sqlalchemy.orm import Mapped, mapped_column
import uuid

class Session(db.Model):
    __tablename__ = "sessions"
    
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    messages = db.relationship("Message", back_populates="session", cascade="all, delete-orphan")