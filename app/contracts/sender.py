from typing import Any, Protocol


class EmailSender(Protocol):
    def send(
        self,
        to: list[str],
        subject: str,
        html: str,
        options: dict[str, Any] | None = None,
    ) -> dict[str, Any]: ...

    def send_with_retry(
        self,
        to: list[str],
        subject: str,
        html: str,
        options: dict[str, Any] | None = None,
        max_attempts: int = 3,
    ) -> dict[str, Any]: ...
