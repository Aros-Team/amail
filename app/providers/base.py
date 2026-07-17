from abc import ABC

from app.contracts.sender import EmailSender
from app.contracts.receiver import EmailReceiver


class EmailProvider(ABC):
    name: str
    sender: EmailSender
    receiver: EmailReceiver | None = None
