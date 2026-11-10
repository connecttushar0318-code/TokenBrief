import os
import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import requests
from config import settings

logger = logging.getLogger("tokenbrief.email")

class EmailNotificationService:
    @staticmethod
    def generate_otp_email_html(recipient_username: str, otp_code: str, action_title: str) -> str:
        # Exact Retentrix-style card template
        return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{otp_code} is your {settings.app_name} verification code</title>
</head>
<body style="margin: 0; padding: 0; background-color: #f1f5f9; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; color: #1e293b;">
  <table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0" style="background-color: #f1f5f9; padding: 40px 12px;">
    <tr>
      <td align="center">
        <!-- Main White Card Container -->
        <table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0" style="max-width: 540px; background: #ffffff; border-radius: 16px; overflow: hidden; box-shadow: 0 10px 30px rgba(0, 0, 0, 0.08); border: 1px solid #e2e8f0;">
          
          <!-- Top Blue/Purple Gradient Header -->
          <tr>
            <td style="background: linear-gradient(135deg, #4338ca 0%, #4f46e5 50%, #6366f1 100%); padding: 36px 28px; text-align: center; color: #ffffff;">
              <div style="font-size: 24px; font-weight: 800; color: #ffffff; letter-spacing: -0.3px;">
                &#129504; TokenBrief Intelligence
              </div>
              <div style="font-size: 13px; color: #e0e7ff; margin-top: 6px; font-weight: 500; letter-spacing: 0.3px;">
                Intelligent Document Analysis &amp; RAG Platform
              </div>
            </td>
          </tr>

          <!-- Main Body -->
          <tr>
            <td style="padding: 36px 36px 24px 36px;">
              <h2 style="font-size: 20px; font-weight: 800; color: #0f172a; margin: 0 0 14px 0; letter-spacing: -0.3px;">
                Security Verification Code
              </h2>
              <p style="font-size: 14px; color: #475569; line-height: 1.6; margin: 0 0 26px 0;">
                You requested a one-time passcode to authenticate with your <strong>TokenBrief</strong> account. Enter this code to verify your identity:
              </p>

              <!-- One-Time Passcode Box -->
              <div style="background: #ffffff; border: 1.5px dashed #cbd5e1; border-radius: 12px; padding: 24px 16px; text-align: center; margin: 0 0 26px 0;">
                <div style="font-size: 11px; font-weight: 700; letter-spacing: 2px; text-transform: uppercase; color: #64748b; margin-bottom: 12px;">
                  ONE-TIME PASSCODE
                </div>
                <div style="font-family: 'SF Mono', Monaco, Consolas, 'Fira Code', monospace; font-size: 38px; font-weight: 900; letter-spacing: 10px; color: #4338ca; padding-left: 10px; margin-bottom: 14px;">
                  {otp_code}
                </div>
                <div>
                  <span style="display: inline-block; background: #fef3c7; border: 1px solid #fde68a; border-radius: 9999px; padding: 4px 14px; font-size: 12px; font-weight: 600; color: #b45309;">
                    &#9201; Expires in {settings.otp_expiration_minutes} minutes
                  </span>
                </div>
              </div>

              <!-- Security Guidelines Box -->
              <div style="background: #f8fafc; border-left: 4px solid #6366f1; border-radius: 0 8px 8px 0; padding: 14px 18px; margin: 0 0 10px 0;">
                <div style="font-size: 13px; font-weight: 700; color: #1e293b; margin-bottom: 8px;">
                  &#128274; Security Guidelines:
                </div>
                <ul style="margin: 0; padding-left: 18px; font-size: 12px; color: #64748b; line-height: 1.6;">
                  <li>Never share this code with anyone.</li>
                  <li><strong>TokenBrief</strong> staff will never ask for your verification code.</li>
                  <li>If you did not request this code, you can safely ignore this email.</li>
                </ul>
              </div>
            </td>
          </tr>

          <!-- Footer -->
          <tr>
            <td style="padding: 24px 36px 30px 36px; border-top: 1px solid #f1f5f9; text-align: center; background: #ffffff;">
              <p style="font-size: 11px; color: #64748b; margin: 0; line-height: 1.6;">
                &copy; 2026 <strong>TokenBrief</strong> Intelligence Systems. All rights reserved.<br />
                Enterprise Multi-Agent Document Intelligence Platform.
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
            if response.status_code in (200, 201):
                logger.info(f"Email successfully delivered via Resend HTTPS to {recipient_email}")
                return True
            else:
                logger.warning(f"Resend rejected: status={response.status_code}, body={response.text}")
                return False
        except Exception as ex:
            logger.error(f"Resend HTTPS dispatch failed: {ex}")
            return False

    @classmethod
    def send_via_gmail_smtp(
        cls,
        recipient_email: str,
        subject: str,
        html_content: str
    ) -> bool:
        if not settings.gmail_app_password or not settings.gmail_sender_email:
            return False

        clean_pwd = settings.gmail_app_password.replace(" ", "").strip()
        sender_email = settings.gmail_sender_email.strip()
        target_email = recipient_email.strip()

        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = f"TokenBrief Intelligence <{sender_email}>"
            msg["To"] = target_email

            part_html = MIMEText(html_content, "html", "utf-8")
            msg.attach(part_html)

            # Try SSL 465 first with 5s timeout
            try:
                with smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=5) as server:
                    server.login(sender_email, clean_pwd)
                    server.sendmail(sender_email, target_email, msg.as_string())
                logger.info(f"Email delivered via Gmail SSL 465 to {target_email}")
                return True
            except Exception:
                with smtplib.SMTP("smtp.gmail.com", 587, timeout=5) as server:
                    server.starttls()
                    server.login(sender_email, clean_pwd)
                    server.sendmail(sender_email, target_email, msg.as_string())
                logger.info(f"Email delivered via Gmail TLS 587 to {target_email}")
                return True
        except Exception as ex:
            logger.error(f"Gmail SMTP dispatch failed: {ex}")
            return False

    @classmethod
    def send_verification_email(
        cls,
        recipient_email: str,
        recipient_username: str,
        otp_code: str,
        action_title: str = "Email Verification"
    ) -> bool:
        # Match exact subject format from Retentrix: "394825 is your TokenBrief verification code"
        subject = f"{otp_code} is your {settings.app_name} verification code"
        html_body = cls.generate_otp_email_html(
            recipient_username=recipient_username,
            otp_code=otp_code,
            action_title=action_title
        )

        # 1. Primary on Cloud: Resend API over HTTPS (Port 443 - works on Render Free Tier!)
        if settings.resend_api_key:
            sent = cls.send_via_resend(recipient_email, subject, html_body)
            if sent:
                return True

        # 2. Secondary fallback: Gmail SMTP (works on local machine or unblocked hosts)
        if settings.gmail_app_password:
            sent = cls.send_via_gmail_smtp(recipient_email, subject, html_body)
            if sent:
                return True

        return False
