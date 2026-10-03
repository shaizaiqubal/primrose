from fastapi import HTTPException, status
import smtplib
from email.message import EmailMessage
from backend.app.config import SENDER_PASSWORD

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
  @import url('https://fonts.googleapis.com/css2?family=Work+Sans:wght@300;400;500;600&display=swap');
 
  @font-face {
    font-family: 'Anvers';
    src: url('https://YOUR-DOMAIN/fonts/Anvers-Regular.otf') format('opentype');
    font-display: swap;
  }
 
  body, table, td, a { -webkit-text-size-adjust: 100%; }
 
  @media only screen and (max-width: 560px) {
    .container { width: 100% !important; }
    .pad { padding-left: 24px !important; padding-right: 24px !important; }
  }
</style>
</head>
<body style="margin:0; padding:0; background-color:#141C1A;">
 
<div style="display:none; max-height:0; overflow:hidden; opacity:0;">
  Verify your email to finish setting up Primrose.
</div>
 
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" style="background-color:#141C1A;">
  <tr>
    <td align="center" style="padding:48px 16px;">
 
      <table role="presentation" class="container" width="520" cellpadding="0" cellspacing="0" border="0"
             style="width:520px; max-width:100%; background-color:#141C1A; border:1px solid #2C3836; border-radius:4px;">
 
        <tr>
          <td class="pad" align="center" style="padding:44px 40px 0 40px;">
            <div style="font-family:'Anvers', Georgia, 'Times New Roman', serif; font-size:30px; line-height:1.2; letter-spacing:0.5px; color:#F0EBE1; text-align:center;">
              <span style="display:inline-block; width:9px; height:9px; border-radius:50%; background-color:#a38f53; vertical-align:middle; margin-right:12px; position:relative; top:-2px;"></span>Primrose
            </div>
          </td>
        </tr>
 
        <tr>
          <td class="pad" align="center" style="padding:36px 40px 0 40px; font-family:'Work Sans', system-ui, -apple-system, 'Segoe UI', Arial, sans-serif;">
            <h2 style="margin:0 0 16px 0; font-size:20px; font-weight:500; line-height:1.3; color:#F0EBE1; text-align:center;">
              Welcome to Primrose
            </h2>
            <p style="margin:0 0 28px 0; font-size:15px; font-weight:400; line-height:1.6; color:#F0EBE1; text-align:center;">
              Thanks for creating an account. Confirm your email address to get started.
            </p>
          </td>
        </tr>
 
        <tr>
          <td class="pad" align="center" style="padding:0 40px;">
            <table role="presentation" cellpadding="0" cellspacing="0" border="0" align="center">
              <tr>
                <td align="center" style="background-color:#a38f53; border-radius:3px;">
                  <a href="{verification_url}"
                     style="display:inline-block; padding:13px 28px; font-family:'Work Sans', system-ui, -apple-system, 'Segoe UI', Arial, sans-serif; font-size:15px; font-weight:500; color:#141C1A; text-decoration:none;">
                    Verify your email
                  </a>
                </td>
              </tr>
            </table>
          </td>
        </tr>
 
        <tr>
          <td class="pad" align="center" style="padding:28px 40px 0 40px; font-family:'Work Sans', system-ui, -apple-system, 'Segoe UI', Arial, sans-serif;">
            <p style="margin:0; font-size:13px; line-height:1.6; color:#7A9490; text-align:center;">
              This link expires in 24 hours.
            </p>
          </td>
        </tr>
 
        <tr>
          <td class="pad" align="center" style="padding:36px 40px 40px 40px; font-family:'Work Sans', system-ui, -apple-system, 'Segoe UI', Arial, sans-serif;">
            <div style="border-top:1px solid #2C3836; padding-top:20px; text-align:center;">
              <p style="margin:0 0 6px 0; font-size:12px; line-height:1.6; color:#7A9490; text-align:center;">
                Button not working? Paste this link into your browser:
              </p>
              <p style="margin:0; font-size:12px; line-height:1.6; word-break:break-all; text-align:center;">
                <a href="{verification_url}" style="color:#a38f53; text-decoration:underline;">{verification_url}</a>
              </p>
              <p style="margin:16px 0 0 0; font-size:12px; line-height:1.6; color:#7A9490; text-align:center;">
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


def render_verification_email(verification_url: str) -> str:
    return VERIFICATION_EMAIL_TEMPLATE.replace("{verification_url}", verification_url)
def send_verification_email(email: str, token: str) -> None:
    if SENDER_PASSWORD is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Email sender is not configured",
        )

    verification_url = f"http://localhost:8000/verify-email?token={token}"

    msg = EmailMessage()
    msg["Subject"] = "Verify your Primrose account"
    msg["From"] = SENDER_EMAIL
    msg["To"] = email

    msg.set_content(
        f"Verify your Primrose account: {verification_url}"
    )

    html_content = render_verification_email(verification_url)
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