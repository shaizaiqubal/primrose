from fastapi import HTTPException, status
import smtplib
from email.message import EmailMessage
from html import escape
from backend.app.config import FRONTEND_URL, SENDER_PASSWORD

SMTP_SERVER = "smtp.gmail.com"  
SMTP_PORT = 587
SENDER_EMAIL = "shaizaiqubal@gmail.com"

VERIFICATION_EMAIL_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="color-scheme" content="dark">
<meta name="supported-color-schemes" content="dark">
<title>Verify your email</title>
<style>
  @import url('https://fonts.googleapis.com/css2?family=Work+Sans:wght@400;600&display=swap');

  body, table, td, a { -webkit-text-size-adjust: 100%; }
  @media only screen and (max-width: 560px) {
    .email-card { width: 100% !important; }
    .email-pad { padding-left: 24px !important; padding-right: 24px !important; }
  }
</style>
</head>
<body style="margin:0; padding:0; background-color:#0C0E14; color:#F1EBDD; font-family:'Work Sans', Arial, sans-serif;">
<div style="display:none; max-height:0; overflow:hidden; opacity:0;">
  Confirm your email address to finish creating your Primrose account.
</div>
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" style="background-color:#0C0E14;">
  <tr>
    <td align="center" style="padding:48px 16px;">
      <table role="presentation" class="email-card" width="560" cellpadding="0" cellspacing="0" border="0" style="width:560px; max-width:100%; background-color:#12141C; border:1px solid #2A2E3D; border-radius:16px;">
        <tr>
          <td class="email-pad" style="padding:40px 40px 0;">
            <div style="font-family:Georgia, 'Times New Roman', serif; font-size:28px; line-height:1.2; color:#F1EBDD;">
              <span style="display:inline-block; width:14px; height:14px; border-radius:50%; border:2px solid #F0D77A; vertical-align:middle; margin-right:10px;"></span>Primrose
            </div>
          </td>
        </tr>
        <tr>
          <td class="email-pad" style="padding:32px 40px 0; font-family:'Work Sans', Arial, sans-serif;">
            <h1 style="margin:0 0 16px; font-family:Georgia, 'Times New Roman', serif; font-size:28px; font-weight:400; line-height:1.2; color:#F1EBDD;">
              Verify your email
            </h1>
            <p style="margin:0; font-size:18px; line-height:1.6; color:#A8AEC2;">
              Confirm <span style="color:#F1EBDD;">{email}</span> to finish creating your Primrose account. The link works once.
            </p>
          </td>
        </tr>
        <tr>
          <td class="email-pad" style="padding:28px 40px 0;">
            <table role="presentation" cellpadding="0" cellspacing="0" border="0" align="center">
              <tr>
                <td align="center" style="background-color:#F0D77A; border-radius:26px;">
                  <a href="{verification_url}" style="display:inline-block; padding:0 32px; height:52px; line-height:52px; font-family:'Work Sans', Arial, sans-serif; font-size:18px; font-weight:600; color:#12141C; text-decoration:none;">
                    Verify my email
                  </a>
                </td>
              </tr>
            </table>
          </td>
        </tr>
        <tr>
          <td class="email-pad" style="padding:28px 40px 40px; font-family:'Work Sans', Arial, sans-serif;">
            <div style="border-top:1px solid #2A2E3D; padding-top:20px;">
              <p style="margin:0 0 6px; font-size:16px; line-height:1.6; color:#A8AEC2;">
                Button not working? Paste this link into your browser:
              </p>
              <p style="margin:0; font-size:16px; line-height:1.6; word-break:break-all;">
                <a href="{verification_url}" style="color:#F0D77A; text-decoration:underline;">{verification_url}</a>
              </p>
              <p style="margin:20px 0 0; font-size:16px; line-height:1.6; color:#A8AEC2;">
                If you did not create a Primrose account, you can ignore this email.
              </p>
            </div>
          </td>
        </tr>
      </table>
    </td>
  </tr>
</table>
</body>
</html>
"""


def render_verification_email(verification_url: str, email: str = "you@example.com") -> str:
    return (
        VERIFICATION_EMAIL_TEMPLATE
        .replace("{verification_url}", verification_url)
        .replace("{email}", escape(email))
    )
def send_verification_email(email: str, token: str) -> None:
    if SENDER_PASSWORD is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Email sender is not configured",
        )

    frontend_url = (FRONTEND_URL or "http://localhost:5173").rstrip("/")
    verification_url = f"{frontend_url}/verify-email?token={token}"

    msg = EmailMessage()
    msg["Subject"] = "Verify your Primrose account"
    msg["From"] = SENDER_EMAIL
    msg["To"] = email

    msg.set_content(
        f"Verify your Primrose account: {verification_url}"
    )

    html_content = render_verification_email(verification_url, email)
    msg.add_alternative(html_content, subtype="html")

    try:
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(SENDER_EMAIL, SENDER_PASSWORD)
            server.send_message(msg)

    except Exception as e:
        print(f"Failed to send verification email: {e}")

        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Failed to send verification email",
        )