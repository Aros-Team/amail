from datetime import datetime, timezone
from typing import Any

from app.logging_config import get_logger
from app.models.schemas import EmailResponse

log = get_logger(__name__)


def build_failure_report(results: list[EmailResponse]) -> str:
    failed = [r for r in results if not r.success]
    if not failed:
        return ""

    rows = "".join(
        f"<tr><td>{r.to or 'N/A'}</td><td>{r.message}</td><td>{datetime.now(timezone.utc).isoformat()}</td></tr>"
        for r in failed
    )

    return f"""<!DOCTYPE html>
<html lang="en">
<head><meta charset="UTF-8"><title>Batch Send Failure Report</title></head>
<body style="font-family:Arial,sans-serif;padding:20px">
<h2>Batch Send Failure Report</h2>
<p>{len(failed)} email(s) failed to send.</p>
<table border="1" cellpadding="8" cellspacing="0" style="border-collapse:collapse;width:100%">
<tr style="background:#f44336;color:#fff"><th>To</th><th>Error</th><th>Timestamp</th></tr>
{rows}
</table>
</body></html>"""


def send_failure_report(
    results: list[EmailResponse], admin_email: str, sender: Any
) -> None:
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
