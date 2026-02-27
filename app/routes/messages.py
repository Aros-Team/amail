from fastapi import APIRouter, Depends, HTTPException, Request

from app.contracts.sender import EmailSender
from app.contracts.receiver import EmailReceiver
from app.models.schemas import (
    EmailRequest,
    EmailResponse,
    TemplatesResponse,
    TemplateInfo,
)
from app.providers import get_sender, get_receiver
from app.security import get_current_user
from app.services.templates import get_templates, render_template

router = APIRouter(prefix="/api", tags=["messages"])


@router.get("/templates", response_model=TemplatesResponse)
def list_templates():
    templates = get_templates()
    return TemplatesResponse(
        templates=[TemplateInfo(name=name, description=desc) for name, desc in templates.items()]
    )


@router.post("/send", response_model=EmailResponse)
def send_email(
    request: EmailRequest,
    user: dict = Depends(get_current_user),
    sender: EmailSender = Depends(get_sender),
):
    templates = get_templates()

    if request.template not in templates:
        raise HTTPException(status_code=400, detail=f"Template '{request.template}' not found")

    try:
        html_content = render_template(request.template, request.data)
        email_id = sender.send(request.to, request.subject, html_content)

        return EmailResponse(
            success=True,
            message="Email sent successfully",
            email_id=email_id,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/receive")
async def receive_email(
    request: Request,
    user: dict = Depends(get_current_user),
    receiver: EmailReceiver = Depends(get_receiver),
):
    payload = await request.json()

    try:
        result = receiver.receive(payload)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
