import os
import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage
import requests
from config import settings

logger = logging.getLogger("tokenbrief.email")

class EmailNotificationService:
    @staticmethod
    def generate_otp_email_html(recipient_username: str, otp_code: str, action_title: str) -> str:
        return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>TokenBrief Verification</title>
</head>
<body style="margin: 0; padding: 0; background-color: #070a12; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; color: #f1f5f9;">
  <table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0" style="background-color: #070a12; padding: 32px 12px;">
    <tr>
      <td align="center">
        <!-- Main Card Container -->
        <table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0" style="max-width: 540px; background: #0f172a; border: 1px solid rgba(99, 102, 241, 0.35); border-radius: 20px; overflow: hidden; box-shadow: 0 20px 50px rgba(0, 0, 0, 0.6);">
          
          <!-- Accent Top Bar -->
          <tr>
            <td height="5" style="background: linear-gradient(90deg, #6366f1 0%, #a855f7 50%, #f59e0b 100%);"></td>
          </tr>

          <!-- Header & Logo -->
          <tr>
            <td style="padding: 36px 32px 12px 32px; text-align: center;">
              <!-- Logo Container -->
              <table role="presentation" cellspacing="0" cellpadding="0" border="0" align="center" style="margin: 0 auto 16px auto;">
                <tr>
                  <td align="center">
                    <img src="cid:tokenbrief_logo" onerror="this.src='https://token-brief-tushaar.vercel.app/apple-touch-icon.png'" width="64" height="64" alt="TokenBrief Logo" style="display: block; border-radius: 14px; border: 2px solid #f59e0b; box-shadow: 0 6px 20px rgba(245, 158, 11, 0.45); margin: 0 auto;" />
                  </td>
                </tr>
              </table>

              <!-- Brand Pill Badge -->
              <div style="display: inline-block; padding: 5px 14px; background: rgba(99, 102, 241, 0.15); border: 1px solid rgba(99, 102, 241, 0.45); border-radius: 9999px; font-size: 11px; font-weight: 700; letter-spacing: 1.8px; text-transform: uppercase; color: #a5b4fc; margin-bottom: 18px;">
                TOKENBRIEF WORKSPACE
              </div>

              <!-- Main Heading -->
              <h1 style="font-size: 25px; font-weight: 800; color: #ffffff; margin: 0 0 10px 0; letter-spacing: -0.4px;">
                {action_title}
              </h1>
              <p style="font-size: 14px; color: #94a3b8; line-height: 1.6; margin: 0 0 8px 0;">
                Hello <strong style="color: #f8fafc;">{recipient_username}</strong>, your one-time verification passcode (OTP) has been generated. Use it below to proceed.
              </p>
            </td>
          </tr>

          <!-- OTP Code Box -->
          <tr>
            <td style="padding: 16px 32px 24px 32px; text-align: center;">
              <div style="background: #030712; border: 2px dashed rgba(99, 102, 241, 0.55); border-radius: 16px; padding: 24px 16px; text-align: center;">
                <div style="font-family: 'SF Mono', Monaco, Consolas, 'Fira Code', monospace; font-size: 40px; font-weight: 900; letter-spacing: 12px; color: #38bdf8; text-shadow: 0 0 24px rgba(56, 189, 248, 0.45); padding-left: 12px;">
                  {otp_code}
                </div>
                <div style="font-size: 12px; color: #64748b; margin-top: 12px; font-weight: 500;">
                  Valid for {settings.otp_expiration_minutes} minutes &bull; Single-use only
                </div>
              </div>
            </td>
          </tr>

          <!-- Security Tip Box -->
          <tr>
            <td style="padding: 0 32px 28px 32px;">
              <table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0" style="background: rgba(239, 68, 68, 0.08); border-left: 3px solid #ef4444; border-radius: 0 8px 8px 0; padding: 12px 16px;">
                <tr>
                  <td style="font-size: 12px; color: #fca5a5; line-height: 1.5;">
                    <strong>Security Notice:</strong> Never share this verification code with anyone. TokenBrief staff will never ask you for your OTP.
                  </td>
                </tr>
              </table>
            </td>
          </tr>

          <!-- Footer -->
          <tr>
            <td style="padding: 22px 32px 28px 32px; border-top: 1px solid rgba(148, 163, 184, 0.12); text-align: center; background: #0b1120;">
              <p style="font-size: 11px; color: #64748b; margin: 0; line-height: 1.6;">
                Dispatched by <strong>TokenBrief Document Intelligence Engine</strong><br />
                Sent via Secure SMTP Relay &bull; {settings.gmail_sender_email}
              </p>
            </td>
          </tr>

        </table>
      </td>
    </tr>
  </table>
</body>
</html>"""

    @classmethod
    def _attach_logo_image(cls, msg_root: MIMEMultipart) -> None:
        logo_paths = [
            "static/logo.png",
            "frontend/public/apple-touch-icon.png",
            "frontend/public/icon.png"
        ]
        for p in logo_paths:
            if os.path.exists(p):
                try:
                    with open(p, "rb") as f:
                        img_data = f.read()
                    img_part = MIMEImage(img_data)
                    img_part.add_header("Content-ID", "<tokenbrief_logo>")
                    img_part.add_header("Content-Disposition", "inline", filename="logo.png")
                    msg_root.attach(img_part)
                    return
                except Exception as ex:
                    logger.debug(f"Could not attach local logo {p}: {ex}")

    @classmethod
    def send_via_gmail_smtp(
        cls,
        recipient_email: str,
        subject: str,
        html_content: str
    ) -> bool:
        if not settings.gmail_app_password or not settings.gmail_sender_email:
            logger.warning("Gmail SMTP credentials missing in configuration.")
            return False

        clean_pwd = settings.gmail_app_password.replace(" ", "").strip()
        sender_email = settings.gmail_sender_email.strip()
        target_email = recipient_email.strip()

        try:
            msg_root = MIMEMultipart("related")
            msg_root["Subject"] = subject
            msg_root["From"] = f"TokenBrief Workspace <{sender_email}>"
            msg_root["To"] = target_email

            part_html = MIMEText(html_content, "html", "utf-8")
            msg_root.attach(part_html)
            cls._attach_logo_image(msg_root)

            # Try Port 465 (SSL) first - fastest & works cleanly through cloud network boundaries
            try:
                with smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=10) as server:
                    server.login(sender_email, clean_pwd)
                    server.sendmail(sender_email, target_email, msg_root.as_string())
                logger.info(f"Email successfully delivered via Gmail SMTP SSL (465) to {target_email}")
                return True
            except Exception as ssl_ex:
                logger.warning(f"Gmail SSL 465 failed ({ssl_ex}), attempting STARTTLS port 587...")
                with smtplib.SMTP("smtp.gmail.com", 587, timeout=10) as server:
                    server.starttls()
                    server.login(sender_email, clean_pwd)
                    server.sendmail(sender_email, target_email, msg_root.as_string())
                logger.info(f"Email successfully delivered via Gmail SMTP TLS (587) to {target_email}")
                return True
        except Exception as ex:
            logger.error(f"Gmail SMTP dispatch failed completely: {ex}")
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
            "to": [recipient_email.strip()],
            "reply_to": settings.gmail_sender_email.strip(),
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
        except Exception as ex:
            logger.error(f"Resend dispatch failed: {ex}")
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

        # 1. Prefer Gmail SMTP: Can send from connect.tushar0318@gmail.com to ANY email in the world
        if settings.gmail_app_password:
            sent = cls.send_via_gmail_smtp(recipient_email, subject, html_body)
            if sent:
                return True

        # 2. Secondary fallback: Resend API
        return cls.send_via_resend(recipient_email, subject, html_body)
