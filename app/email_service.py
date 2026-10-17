"""
app/email_service.py
================================================================================
EMAIL DISPATCH SERVICE
Sends actual email verification OTPs and notification alerts to users using
Python's built-in smtplib (works with Gmail, Office 365, SendGrid, Amazon SES, etc.)
Falls back gracefully to development simulation mode when SMTP credentials are not yet configured.
================================================================================
"""

import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import site_config


def is_smtp_configured() -> bool:
    """Checks whether valid SMTP dispatch credentials have been supplied."""
    server = os.environ.get("SMTP_SERVER", getattr(site_config, "SMTP_SERVER", "")).strip()
    user = os.environ.get("SMTP_USERNAME", getattr(site_config, "SMTP_USERNAME", "")).strip()
    pwd = os.environ.get("SMTP_PASSWORD", getattr(site_config, "SMTP_PASSWORD", "")).strip()
    return bool(server and user and pwd)


def send_otp_email(recipient_email: str, otp_code: str, recipient_name: str = "Member") -> tuple[bool, str]:
    """
    Sends the 6-digit registration OTP code to recipient_email.
    Returns (success: bool, status_message: str).
    """
    server = os.environ.get("SMTP_SERVER", getattr(site_config, "SMTP_SERVER", "")).strip()
    port = int(os.environ.get("SMTP_PORT", getattr(site_config, "SMTP_PORT", 587)))
    user = os.environ.get("SMTP_USERNAME", getattr(site_config, "SMTP_USERNAME", "")).strip()
    pwd = os.environ.get("SMTP_PASSWORD", getattr(site_config, "SMTP_PASSWORD", "")).strip()
    from_email = os.environ.get("SMTP_FROM_EMAIL", getattr(site_config, "SMTP_FROM_EMAIL", "")).strip() or user or "noreply@aitpune.edu.in"
    site_name = getattr(site_config, "SITE_NAME", "NovumHub")
    college_name = getattr(site_config, "COLLEGE_NAME", "Army Institute of Technology (AIT), Pune")

    if not is_smtp_configured():
        # Simulation / Development Mode: log to console
        print(f"\n[EMAIL SIMULATION] SMTP not configured.")
        print(f" -> To: {recipient_email}")
        print(f" -> Subject: Your {site_name} Verification Code: {otp_code}")
        print(f" -> Code: {otp_code}\n")
        return False, "SMTP server not configured. Verification code displayed for development/demo."

    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = f"Your {site_name} Verification Code: {otp_code}"
        msg["From"] = f"{site_name} Portal <{from_email}>"
        msg["To"] = recipient_email

        plain_text = (
            f"Hello {recipient_name},\n\n"
            f"Your 6-digit email confirmation code for {site_name} is: {otp_code}\n\n"
            f"Please enter this code on the registration page to activate your account.\n"
            f"If you did not request this, you can safely ignore this email.\n\n"
            f"— {college_name}"
        )

        html_body = f"""
        <!DOCTYPE html>
        <html>
        <head>
          <meta charset="utf-8">
          <style>
            body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; background-color: #f4f4f0; margin: 0; padding: 20px; }}
            .card {{ max-width: 540px; margin: 0 auto; background: #ffffff; border: 2px solid #000000; box-shadow: 4px 4px 0px #000000; padding: 30px; }}
            .brand {{ font-size: 20px; font-weight: 800; text-transform: uppercase; letter-spacing: -0.5px; margin-bottom: 5px; }}
            .sub-brand {{ font-size: 13px; color: #666; font-family: monospace; margin-bottom: 25px; }}
            .code-box {{ background: #fafaf8; border: 2px solid #000000; box-shadow: 3px 3px 0px #000000; padding: 18px; text-align: center; margin: 25px 0; }}
            .otp-digits {{ font-family: 'Courier New', Courier, monospace; font-size: 32px; font-weight: bold; letter-spacing: 10px; color: #000000; }}
            .footer {{ font-size: 12px; color: #777; margin-top: 30px; border-top: 1px dashed #ccc; padding-top: 15px; font-family: monospace; }}
          </style>
        </head>
        <body>
          <div class="card">
            <div class="brand">{site_name}</div>
            <div class="sub-brand">[{college_name}]</div>
            <p>Hello <strong>{recipient_name}</strong>,</p>
            <p>Thank you for initiating your institutional account clearance. Use the 6-digit confirmation code below to verify your email address:</p>
            
            <div class="code-box">
              <div class="otp-digits">{otp_code}</div>
            </div>

            <p style="font-size: 14px; color: #444;">This one-time verification code is valid for 15 minutes. Enter this code on the verification page to complete your registration.</p>
            
            <div class="footer">
              If you did not initiate this registration, please disregard this message.<br>
              &copy; {college_name} - All rights reserved.
            </div>
          </div>
        </body>
        </html>
        """

        msg.attach(MIMEText(plain_text, "plain", "utf-8"))
        msg.attach(MIMEText(html_body, "html", "utf-8"))

        with smtplib.SMTP(server, port, timeout=12) as smtp_conn:
            smtp_conn.ehlo()
            if port == 587 or getattr(site_config, "SMTP_USE_TLS", True):
                smtp_conn.starttls()
                smtp_conn.ehlo()
            smtp_conn.login(user, pwd)
            smtp_conn.sendmail(from_email, [recipient_email], msg.as_string())

        print(f"[EMAIL SUCCESS] Dispatched OTP code to {recipient_email} via {server}:{port}")
        return True, f"Verification code sent directly to {recipient_email}."

    except Exception as e:
        err_msg = f"Failed to send email via SMTP ({e})."
        print(f"[EMAIL ERROR] {err_msg}")
        return False, err_msg
