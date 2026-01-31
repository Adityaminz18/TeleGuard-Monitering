import asyncio
import smtplib
from email.message import EmailMessage
import ssl
from app.core.config import settings

async def test_email():
    print("Testing Email Configuration...")
    print(f"Server: {settings.SMTP_SERVER}:{settings.SMTP_PORT}")
    print(f"User: {settings.SMTP_USER}")
    
    to_email = "adityaminz18@gmail.com" # Using user from DB check
    subject = "Test Email from TeleGuard Debugger"
    content = "If you receive this, SMTP is working!"

    msg = EmailMessage()
    msg['Subject'] = subject
    msg['From'] = settings.EMAILS_FROM_EMAIL or "noreply@tele-guard.com"
    msg['To'] = to_email
    msg.set_content(content)

    try:
        if settings.SMTP_PORT == 465:
            context = ssl.create_default_context()
            with smtplib.SMTP_SSL(settings.SMTP_SERVER, settings.SMTP_PORT, context=context) as server:
                server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
                server.send_message(msg)
        else:
            with smtplib.SMTP(settings.SMTP_SERVER, settings.SMTP_PORT) as server:
                server.starttls()
                server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
                server.send_message(msg)
        print("Email sent successfully!")
    except Exception as e:
        print(f"Email FAILED: {e}")

if __name__ == "__main__":
    asyncio.run(test_email())
