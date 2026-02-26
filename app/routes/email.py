from fastapi import APIRouter, HTTPException
from app.models.schemas import EmailRequest, EmailResponse, TemplatesResponse, TemplateInfo
from app.services.templates import render_template, get_templates
from app.services.resend_client import resend_client

router = APIRouter(prefix="/api", tags=["email"])


@router.get("/templates", response_model=TemplatesResponse)
def list_templates():
    templates = get_templates()
    return TemplatesResponse(
        templates=[TemplateInfo(name=name, description=desc) for name, desc in templates.items()]
    )


@router.post("/send", response_model=EmailResponse)
def send_email(request: EmailRequest):
    templates = get_templates()
    
    if request.template not in templates:
        raise HTTPException(status_code=400, detail=f"Template '{request.template}' no encontrado")
    
    try:
        html_content = render_template(request.template, request.data)
        response = resend_client.send_email(request, html_content)
        
        return EmailResponse(
            success=True,
            message="Email enviado exitosamente",
            email_id=response.get("id")
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
