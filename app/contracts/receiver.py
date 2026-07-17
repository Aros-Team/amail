from typing import Any, Protocol


class EmailReceiver(Protocol):
    def receive(self, payload: dict[str, Any]) -> dict[str, Any]: ...
