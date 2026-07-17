from typing import Any

from app.config import get_settings
from app.models.schemas import (
    BatchEmailRequest,
    BatchReport,
    EmailRequest,
    EmailResponse,
)
from app.providers import get_provider
from app.providers.base import EmailProvider
from app.services.batch_reporter import send_failure_report
from app.services.templates import render_template
from app.logging_config import get_logger

log = get_logger(__name__)


class EmailService:
    def __init__(self, provider: EmailProvider | None = None) -> None:
        self._provider = provider or get_provider()
        self.sender = self._provider.sender
        self.receiver = self._provider.receiver

    def send(self, req: EmailRequest) -> EmailResponse:
        to_list = [req.to] if isinstance(req.to, str) else req.to

        options: dict[str, Any] = {}
        if req.cc:
            options["cc"] = [str(e) for e in req.cc]
        if req.bcc:
            options["bcc"] = [str(e) for e in req.bcc]
        if req.reply_to:
            options["reply_to"] = str(req.reply_to)
        if req.from_email:
            options["from_email"] = str(req.from_email)

        template_data = req.data.copy()
        template_data["lang"] = req.lang
        html_content = render_template(req.template, template_data)

        try:
            result = self.sender.send_with_retry(
                to=to_list,
                subject=req.subject,
                html=html_content,
                options=options,
            )
            return EmailResponse(
                success=True,
                message="Email sent successfully",
                email_id=result.get("id", ""),
                request_id=result.get("request_id", ""),
                to=",".join(to_list),
            )
        except Exception as e:
            log.error("email_send_error", error=str(e), to=to_list)
            return EmailResponse(
                success=False,
                message=str(e),
                to=",".join(to_list),
            )

    def send_batch(self, req: BatchEmailRequest) -> BatchReport:
        results: list[EmailResponse] = []

        for email_req in req.emails:
            resp = self.send(email_req)
            results.append(resp)
            if not resp.success and not req.continue_on_error:
                break

        succeeded = sum(1 for r in results if r.success)
        failed = sum(1 for r in results if not r.success)

        report = BatchReport(
            total=len(req.emails),
            succeeded=succeeded,
            failed=failed,
            results=results,
            forwarded_to_admin=False,
        )

        if failed > 0:
            settings = get_settings()
            if settings.admin_email:
                send_failure_report(results, settings.admin_email, self.sender)
                report.forwarded_to_admin = True
                report.admin_email = settings.admin_email

        return report

    def receive_webhook(self, payload: dict[str, Any]) -> dict[str, Any]:
        if self.receiver is None:
            return {"status": "error", "reason": "no receiver configured"}
        return self.receiver.receive(payload)
