from fastapi import APIRouter, Depends, HTTPException, Request
import json
import resend

from app.config import get_settings
from app.contracts.sender import EmailSender
from app.contracts.receiver import EmailReceiver
from app.models.schemas import (
    EmailRequest,
    EmailResponse,
    TemplatesResponse,
    TemplateInfo,
    WebhookPayload,
)
from app.providers import get_sender, get_receiver
from app.services.templates import get_templates, render_template

router = APIRouter(prefix="/api", tags=["messages"])


@router.get("/templates", response_model=TemplatesResponse)
def list_templates():
    templates = get_templates()
    return TemplatesResponse(
        templates=[
            TemplateInfo(name=name, description=info["description"], variables=info["variables"])
            for name, info in templates.items()
        ]
    )


@router.post("/send", response_model=EmailResponse)
def send_email(
    request: EmailRequest,
    sender: EmailSender = Depends(get_sender),
):
    templates = get_templates()

    if request.template not in templates:
        raise HTTPException(status_code=400, detail=f"Template '{request.template}' not found")

    try:
        html_content = render_template(request.template, request.data)
        result = sender.send_with_retry(request.to, request.subject, html_content)

        return EmailResponse(
            success=True,
            message="Email sent successfully",
            email_id=result.get("id", ""),
            request_id=result.get("request_id", ""),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/receive")
async def receive_email(request: Request, receiver: EmailReceiver = Depends(get_receiver)):
    settings = get_settings()

    svix_id = request.headers.get("svix-id")
    svix_timestamp = request.headers.get("svix-timestamp")
    svix_signature = request.headers.get("svix-signature")

    if not all([svix_id, svix_timestamp, svix_signature]):
        raise HTTPException(status_code=400, detail="Missing Svix webhook headers")

    raw_body = await request.body()

    try:
        verified = resend.webhooks.verify(
            payload=raw_body,
            headers={
                "id": svix_id,
                "timestamp": svix_timestamp,
                "signature": svix_signature,
            },
            secret=settings.RESEND_WEBHOOK_SECRET,
        )
    except Exception:
        raise HTTPException(status_code=400, detail="Webhook signature verification failed")

    try:
        payload_dict = json.loads(verified) if isinstance(verified, str) else verified
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid webhook payload")

    try:
        result = receiver.receive(payload_dict)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))