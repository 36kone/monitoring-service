from fastapi_mail import ConnectionConfig, FastMail, MessageSchema, MessageType
from jinja2 import Template
from pydantic import EmailStr

from app.core.config import settings

conf = ConnectionConfig(
    MAIL_USERNAME=settings.MAIL_USER,
    MAIL_PASSWORD=settings.MAIL_PASS,
    MAIL_FROM=settings.MAIL_FROM,
    MAIL_SERVER=settings.MAIL_HOST,
    MAIL_PORT=settings.MAIL_PORT,
    MAIL_STARTTLS=False,
    MAIL_SSL_TLS=True,
    USE_CREDENTIALS=True,
    VALIDATE_CERTS=True,
)


class EmailSender:
    def __init__(self):
        self.mailer = FastMail(conf)

    async def send_email(self, subject: str, email_to: EmailStr, template_path: str, context: dict):
        try:
            with open(template_path, encoding="utf-8") as file:
                template = Template(file.read())
            html_content = template.render(**context)

            message = MessageSchema(
                subject=subject,
                recipients=[email_to],
                body=html_content,
                subtype=MessageType.html,
            )
            await self.mailer.send_message(message)

        except Exception as e:
            raise e
