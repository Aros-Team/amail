from fastapi import APIRouter, Request, HTTPException
from app.config import get_settings
from app.services.resend_client import resend_client

router = APIRouter(prefix="/api", tags=["webhook"])


@router.post("/webhook")
async def resend_webhook(request: Request):
    settings = get_settings()
    
    payload = await request.json()
    
    event_type = payload.get("type")
    
    if event_type == "email.received":
        email_data = payload.get("data", {})
        from_email = email_data.get("from", "")
        subject = email_data.get("subject", "Sin asunto")
        html = email_data.get("html", "")
        
        if from_email in settings.webhook_allowed_emails:
            try:
                resend_client.forward_email(
                    to_email=settings.FORWARD_TO_EMAIL,
                    subject=subject,
                    html_content=html
                )
                return {"status": "forwarded"}
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))
        
        return {"status": "ignored", "reason": "email not in allowed list"}
    
    return {"status": "ignored", "reason": "event type not supported"}
