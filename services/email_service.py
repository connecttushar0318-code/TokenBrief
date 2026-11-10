import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import requests
from config import settings

class EmailNotificationService:
    @staticmethod
    def generate_otp_email_html(recipient_username: str, otp_code: str, action_title: str) -> str:
        return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>TokenBrief Verification</title>
  <style>
    body {{
      margin: 0;
      padding: 0;
      background-color: #090d16;
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
      color: #f1f5f9;
    }}
    .email-container {{
      max-width: 580px;
      margin: 40px auto;
      background: linear-gradient(135deg, rgba(30, 41, 59, 0.7) 0%, rgba(15, 23, 42, 0.9) 100%);
      border: 1px solid rgba(99, 102, 241, 0.25);
      border-radius: 20px;
      padding: 40px 32px;
      box-shadow: 0 20px 50px rgba(0, 0, 0, 0.5), 0 0 40px rgba(99, 102, 241, 0.15);
    }}
    .brand-badge {{
      display: inline-block;
      padding: 6px 14px;
      background: linear-gradient(90deg, #6366f1, #a855f7);
      color: #ffffff;
      font-weight: 700;
      font-size: 13px;
      letter-spacing: 1.5px;
      text-transform: uppercase;
      border-radius: 9999px;
      margin-bottom: 24px;
    }}
    .headline {{
      font-size: 26px;
      font-weight: 800;
      color: #ffffff;
      margin: 0 0 12px 0;
      letter-spacing: -0.5px;
    }}
    .subtext {{
      font-size: 15px;
      color: #94a3b8;
      line-height: 1.6;
      margin-bottom: 32px;
    }}
    .otp-wrapper {{
      background: rgba(15, 23, 42, 0.85);
      border: 2px dashed rgba(99, 102, 241, 0.5);
      border-radius: 16px;
      padding: 24px;
      text-align: center;
      margin: 28px 0;
    }}
    .otp-code {{
      font-family: 'SF Mono', Monaco, Inconsolata, 'Fira Code', monospace;
      font-size: 38px;
      font-weight: 900;
      letter-spacing: 10px;
      color: #38bdf8;
      text-shadow: 0 0 20px rgba(56, 189, 248, 0.4);
      margin: 0;
    }}
    .otp-note {{
      font-size: 13px;
      color: #64748b;
      margin-top: 10px;
    }}
    .security-notice {{
      background: rgba(239, 68, 68, 0.1);
      border-left: 3px solid #ef4444;
      padding: 12px 16px;
      border-radius: 0 8px 8px 0;
      font-size: 13px;
      color: #fca5a5;
      margin: 24px 0;
      line-height: 1.5;
    }}
    .footer {{
      margin-top: 36px;
      padding-top: 20px;
      border-top: 1px solid rgba(148, 163, 184, 0.15);
      font-size: 12px;
      color: #64748b;
      text-align: center;
    }}
  </style>
</head>
<body>
  <div class="email-container">
    <div class="brand-badge">TokenBrief</div>
    <h1 class="headline">{action_title}</h1>
    <p class="subtext">
      Hey <strong>{recipient_username}</strong>, your verification code is ready. Use this one-time passcode (OTP) to securely proceed.
    </p>

    <div class="otp-wrapper">
      <div class="otp-code">{otp_code}</div>
      <div class="otp-note">Valid for {settings.otp_expiration_minutes} minutes</div>
    </div>

    <div class="security-notice">
      Do not share this code with anyone. TokenBrief staff will never ask for your verification code.
    </div>

    <div class="footer">
      Powered by TokenBrief Document Intelligence Engine &bull; Automated System Dispatch
    </div>
  </div>
</body>
</html>"""

    @classmethod
    def send_via_gmail_smtp(
        cls,
        recipient_email: str,
        subject: str,
        html_content: str
    ) -> bool:
        if not settings.gmail_app_password or not settings.gmail_sender_email:
            return False

        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = f"TokenBrief <{settings.gmail_sender_email}>"
            msg["To"] = recipient_email

            part = MIMEText(html_content, "html")
            msg.attach(part)

            clean_pwd = settings.gmail_app_password.replace(" ", "").strip()
            try:
                with smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=7) as server:
                    server.login(settings.gmail_sender_email.strip(), clean_pwd)
                    server.sendmail(settings.gmail_sender_email.strip(), recipient_email.strip(), msg.as_string())
                return True
            except Exception:
                try:
                    with smtplib.SMTP("smtp.gmail.com", 587, timeout=5) as server:
                        server.starttls()
                        server.login(settings.gmail_sender_email.strip(), clean_pwd)
                        server.sendmail(settings.gmail_sender_email.strip(), recipient_email.strip(), msg.as_string())
                    return True
                except Exception:
                    return False
        except Exception:
            return False

    @classmethod
    def send_via_resend(
        cls,
        recipient_email: str,
        subject: str,
        html_content: str
    ) -> bool:
        if not settings.resend_api_key:
            return False

        email_payload = {
            "from": settings.resend_from_email,
            "to": [recipient_email],
            "reply_to": settings.gmail_sender_email,
            "subject": subject,
            "html": html_content
        }

        try:
            response = requests.post(
                "https://api.resend.com/emails",
                json=email_payload,
                headers={
                    "Authorization": f"Bearer {settings.resend_api_key}",
                    "Content-Type": "application/json"
                },
                timeout=10
            )
            return response.status_code in (200, 201)
        except Exception:
            return False

    @classmethod
    def send_verification_email(
        cls,
        recipient_email: str,
        recipient_username: str,
        otp_code: str,
        action_title: str = "Email Verification"
    ) -> bool:
        subject = f"[{otp_code}] Your {settings.app_name} Verification Code"
        html_body = cls.generate_otp_email_html(
            recipient_username=recipient_username,
            otp_code=otp_code,
            action_title=action_title
        )

        if settings.gmail_app_password:
            sent = cls.send_via_gmail_smtp(recipient_email, subject, html_body)
            if sent:
                return True

        return cls.send_via_resend(recipient_email, subject, html_body)
