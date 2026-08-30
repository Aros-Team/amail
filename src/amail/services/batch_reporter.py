"""Batch failure report helpers for the Amail service."""

from datetime import UTC, datetime

from amail.contracts.sender import EmailSender
from amail.logging_config import get_logger
from amail.models.schemas import EmailResponse

log = get_logger(__name__)


def build_failure_report(results: list[EmailResponse]) -> str:
    """Build an HTML failure report for failed batch sends, or an empty string."""
    failed = [r for r in results if not r.success]
    if not failed:
        return ""

    rows = "".join(
        f"<tr><td>{r.to or 'N/A'}</td>"
        f"<td>{r.message}</td>"
        f"<td>{datetime.now(UTC).isoformat()}</td></tr>"
        for r in failed
    )

    return (
        "<!DOCTYPE html>\n"
        '<html lang="en">\n'
        '<head><meta charset="UTF-8"><title>Batch Send Failure Report</title></head>\n'
        '<body style="font-family:Arial,sans-serif;padding:20px">\n'
        "<h2>Batch Send Failure Report</h2>\n"
        f"<p>{len(failed)} email(s) failed to send.</p>\n"
        '<table border="1" cellpadding="8" cellspacing="0" '
        'style="border-collapse:collapse;width:100%">\n'
        '<tr style="background:#f44336;color:#fff">'
        "<th>To</th><th>Error</th><th>Timestamp</th></tr>\n"
        f"{rows}\n"
        "</table>\n"
        "</body></html>"
    )


def send_failure_report(
    results: list[EmailResponse], admin_email: str, sender: EmailSender
) -> None:
    """Send an HTML failure report to the admin email if any sends failed."""
    html = build_failure_report(results)
    if not html:
        return

    try:
        sender.send(
            to=[admin_email],
            subject="[Amail] Batch Send Failure Report",
            html=html,
        )
        log.info(
            "failure_report_sent",
            admin_email=admin_email,
            failed_count=sum(1 for r in results if not r.success),
        )
    except Exception as e:
        log.error("failure_report_send_failed", admin_email=admin_email, error=str(e))
