"""Email receiving contract."""

from typing import Any, Protocol


class EmailReceiver(Protocol):
    """Protocol for email receiving implementations."""

    def receive(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Process an inbound email event and return the outcome."""
        ...
