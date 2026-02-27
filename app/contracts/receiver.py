from typing import Protocol


class EmailReceiver(Protocol):
    def receive(self, payload: dict) -> dict: ...
