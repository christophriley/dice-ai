from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

from .session import Session  # noqa: E402
from .message import Message  # noqa: E402

__all__ = ["db", "Session", "Message"]