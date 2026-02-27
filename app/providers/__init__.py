from app.contracts.sender import EmailSender
from app.contracts.receiver import EmailReceiver
from app.providers.resend import get_resend_sender, get_resend_receiver


def get_sender() -> EmailSender:
    return get_resend_sender()


def get_receiver() -> EmailReceiver:
    return get_resend_receiver()


__all__ = ["get_sender", "get_receiver", "EmailSender", "EmailReceiver"]
