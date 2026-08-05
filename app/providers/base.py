"""Base class for email providers."""

from abc import ABC

from app.contracts.receiver import EmailReceiver
from app.contracts.sender import EmailSender


class EmailProvider(ABC):
    """Base class exposing a sender and an optional receiver."""

    name: str
    sender: EmailSender
    receiver: EmailReceiver | None = None
