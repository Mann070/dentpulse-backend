import smtplib
from email.mime.text import MIMEText
import urllib.parse
import urllib.request
import base64
import os

def send_email_otp(to_email: str, otp: str) -> bool:
    """
    Sends a 4-digit OTP via Email using SMTP (Gmail, SendGrid, etc.).
    Falls back gracefully to terminal console printing if credentials are not configured.
    """
    smtp_server = os.environ.get("SMTP_SERVER", "smtp.gmail.com")
    smtp_port = int(os.environ.get("SMTP_PORT", "587"))
    smtp_username = os.environ.get("SMTP_USERNAME")
    smtp_password = os.environ.get("SMTP_PASSWORD")
    smtp_from = os.environ.get("SMTP_FROM", smtp_username or "no-reply@dentpulse.com")
    
    if not smtp_username or not smtp_password:
        # Graceful sandbox mode fallback
        print("\n" + "="*60)
        print(f"  [DENTPULSE EMAIL MOCK] SMTP credentials not set in .env")
        print(f"  Sent Email OTP to: {to_email}")
        print(f"  VERIFICATION CODE: {otp}")
        print("="*60 + "\n")
        return True
        
    msg = MIMEText(
        f"Your DentPulse AI security verification code is: {otp}.\n\n"
        f"This code will expire in 5 minutes.\n"
        f"If you did not request this code, please secure your account immediately."
    )
    msg["Subject"] = "DentPulse AI - Security Verification Code"
    msg["From"] = smtp_from
    msg["To"] = to_email
    
    try:
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(smtp_username, smtp_password)
        server.sendmail(smtp_from, [to_email], msg.as_string())
        server.quit()
        print(f"\n[DENTPULSE SMTP SUCCESS] Email OTP successfully sent to {to_email}\n")
        return True
    except Exception as e:
        print(f"\n[DENTPULSE SMTP ERROR] Failed to transmit email via SMTP: {e}\n")
        # Log to terminal for developer fallback
        print(f"  [DEVELOPER FALLBACK] VERIFICATION CODE FOR {to_email}: {otp}\n")
        return False

def send_sms_otp(to_phone: str, otp: str) -> bool:
    """
    Sends a 4-digit OTP via SMS using Twilio REST API (using urllib for zero dependency execution).
    Falls back gracefully to terminal console printing if Twilio credentials are not configured.
    """
    account_sid = os.environ.get("TWILIO_ACCOUNT_SID")
    auth_token = os.environ.get("TWILIO_AUTH_TOKEN")
    twilio_number = os.environ.get("TWILIO_PHONE_NUMBER")
    
    if not to_phone:
        print("\n[DENTPULSE TWILIO ERROR] User does not have a registered phone number!\n")
        return False
        
    if not account_sid or not auth_token or not twilio_number:
        # Graceful sandbox mode fallback
        print("\n" + "="*60)
        print(f"  [DENTPULSE Twilio MOCK] Twilio credentials not set in .env")
        print(f"  Sent SMS OTP to: {to_phone}")
        print(f"  VERIFICATION CODE: {otp}")
        print("="*60 + "\n")
        return True
        
    url = f"https://api.twilio.com/2010-04-01/Accounts/{account_sid}/Messages.json"
    
    # Body parameters
    payload = {
        "To": to_phone,
        "From": twilio_number,
        "Body": f"DentPulse AI: Your security verification code is {otp}. Valid for 5 minutes."
    }
    
    data = urllib.parse.urlencode(payload).encode("utf-8")
    
    # Basic Authorization Header
    auth_bytes = f"{account_sid}:{auth_token}".encode("utf-8")
    auth_header = base64.b64encode(auth_bytes).decode("utf-8")
    
    req = urllib.request.Request(url, data=data, method="POST")
    req.add_header("Authorization", f"Basic {auth_header}")
    req.add_header("Content-Type", "application/x-www-form-urlencoded")
    
    try:
        with urllib.request.urlopen(req) as response:
            res_body = response.read().decode("utf-8")
            print(f"\n[DENTPULSE TWILIO SUCCESS] SMS OTP successfully sent to {to_phone}\n")
            return True
    except Exception as e:
        print(f"\n[DENTPULSE TWILIO ERROR] Failed to transmit SMS via Twilio: {e}\n")
        # Log to terminal for developer fallback
        print(f"  [DEVELOPER FALLBACK] VERIFICATION CODE FOR {to_phone}: {otp}\n")
        return False
