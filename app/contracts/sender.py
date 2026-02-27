from typing import Protocol


class EmailSender(Protocol):
    def send(self, to: str, subject: str, html: str) -> str: ...
