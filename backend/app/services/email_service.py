import smtplib
import os
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from dotenv import load_dotenv

load_dotenv()

HOST = os.getenv("EMAIL_HOST", "smtp.gmail.com")
PORT = int(os.getenv("EMAIL_PORT", 587))
USER = os.getenv("EMAIL_USER")
PASS = os.getenv("EMAIL_PASS")
FROM = os.getenv("EMAIL_FROM", USER)


def send_email(to: str, subject: str, html: str):
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = FROM
    msg["To"] = to
    msg.attach(MIMEText(html, "html"))
    with smtplib.SMTP(HOST, PORT) as server:
        server.starttls()
        server.login(USER, PASS)
        server.sendmail(USER, to, msg.as_string())


def test_connection():
    """Run: python -m services.email_service  to test SMTP credentials"""
    print(f"Testing SMTP connection...")
    print(f"USER: {USER}")
    print(f"PASS length: {len(PASS) if PASS else 0} chars")
    try:
        with smtplib.SMTP(HOST, PORT) as server:
            server.starttls()
            server.login(USER, PASS)
            print("SUCCESS - credentials are correct!")
    except Exception as e:
        print(f"FAILED - {e}")


def send_welcome_email(name: str, email: str):
    if not USER or not PASS:
        print("[Email] Skipped: EMAIL_USER/EMAIL_PASS not configured in .env")
        return
    try:
        html = f"""
        <div style="font-family:Segoe UI,sans-serif;max-width:600px;margin:auto;background:#0b0c1e;color:#fff;border-radius:16px;overflow:hidden;">
          <div style="background:linear-gradient(135deg,#00bfff,#0066cc);padding:32px;text-align:center;">
            <h1 style="margin:0;font-size:2rem;letter-spacing:2px;">VISHKART</h1>
            <p style="margin:8px 0 0;opacity:0.9;">Premium Electronics Store</p>
          </div>
          <div style="padding:32px;">
            <h2 style="color:#00bfff;margin-top:0;">Welcome, {name}!</h2>
            <p style="color:#ddd;line-height:1.7;">
              Thank you for registering with <strong>VISHKART</strong>. Your account has been created successfully.
            </p>
            <p style="color:#ddd;line-height:1.7;">
              You can now explore the latest smartphones, laptops, and accessories with unbeatable deals from top brands like Samsung, Apple, OnePlus, and more.
            </p>
            <div style="text-align:center;margin:32px 0;">
              <a href="http://localhost:5500/frontend/index.html"
                 style="background:linear-gradient(45deg,#00bfff,#0066cc);color:#fff;padding:14px 36px;border-radius:50px;text-decoration:none;font-weight:bold;font-size:1rem;">
                Start Shopping
              </a>
            </div>
            <p style="color:#aaa;font-size:0.85rem;">
              If you did not create this account, please ignore this email.
            </p>
          </div>
          <div style="background:#111;padding:16px;text-align:center;color:#555;font-size:0.8rem;">
            &copy; 2025 VISHKART. All rights reserved. | Nagpur, Maharashtra, India
          </div>
        </div>
        """
        send_email(email, "Welcome to VISHKART!", html)
    except Exception as e:
        print(f"[Email] Failed to send welcome email to {email}: {e}")


def send_contact_email(name: str, email: str, phone: str, subject: str, message: str):
    """Send contact form details to the store owner."""
    if not USER or not PASS:
        print("[Email] Skipped: EMAIL_USER/EMAIL_PASS not configured in .env")
        return
    try:
        html = f"""
        <div style="font-family:Segoe UI,sans-serif;max-width:600px;margin:auto;background:#0b0c1e;color:#fff;border-radius:16px;overflow:hidden;">
          <div style="background:linear-gradient(135deg,#00bfff,#0066cc);padding:28px;text-align:center;">
            <h1 style="margin:0;font-size:1.6rem;letter-spacing:2px;">VISHKART</h1>
            <p style="margin:6px 0 0;opacity:0.9;">New Contact Form Submission</p>
          </div>
          <div style="padding:32px;">
            <h2 style="color:#00bfff;margin-top:0;">New Message Received</h2>
            <table style="width:100%;border-collapse:collapse;">
              <tr><td style="padding:10px 0;color:#aaa;width:120px;">Name</td><td style="padding:10px 0;color:#fff;font-weight:600;">{name}</td></tr>
              <tr><td style="padding:10px 0;color:#aaa;">Email</td><td style="padding:10px 0;color:#00bfff;">{email}</td></tr>
              <tr><td style="padding:10px 0;color:#aaa;">Phone</td><td style="padding:10px 0;color:#fff;">{phone or 'Not provided'}</td></tr>
              <tr><td style="padding:10px 0;color:#aaa;">Subject</td><td style="padding:10px 0;color:#fff;">{subject}</td></tr>
            </table>
            <div style="margin-top:20px;background:rgba(0,191,255,0.08);border-left:4px solid #00bfff;border-radius:8px;padding:16px;">
              <p style="color:#aaa;margin:0 0 8px;font-size:0.85rem;">MESSAGE</p>
              <p style="color:#fff;margin:0;line-height:1.7;">{message}</p>
            </div>
            <div style="margin-top:24px;text-align:center;">
              <a href="mailto:{email}" style="background:linear-gradient(45deg,#00bfff,#0066cc);color:#fff;padding:12px 28px;border-radius:50px;text-decoration:none;font-weight:bold;">Reply to {name}</a>
            </div>
          </div>
          <div style="background:#111;padding:14px;text-align:center;color:#555;font-size:0.8rem;">
            &copy; 2025 VISHKART &mdash; Contact Form Notification
          </div>
        </div>
        """
        for recipient in [USER, "akhileshpardeshi3@gmail.com"]:
            send_email(recipient, f"New Contact: {subject}", html)
    except Exception as e:
        print(f"[Email] Failed to send contact notification: {e}")


def send_contact_confirmation(name: str, email: str, subject: str):
    """Send confirmation email to the user who submitted the contact form."""
    if not USER or not PASS:
        return
    try:
        html = f"""
        <div style="font-family:Segoe UI,sans-serif;max-width:600px;margin:auto;background:#0b0c1e;color:#fff;border-radius:16px;overflow:hidden;">
          <div style="background:linear-gradient(135deg,#00bfff,#0066cc);padding:28px;text-align:center;">
            <h1 style="margin:0;font-size:1.6rem;letter-spacing:2px;">VISHKART</h1>
            <p style="margin:6px 0 0;opacity:0.9;">We received your message!</p>
          </div>
          <div style="padding:32px;">
            <h2 style="color:#00bfff;margin-top:0;">Thanks for reaching out, {name}!</h2>
            <p style="color:#ddd;line-height:1.7;">We have received your message regarding <strong style="color:#fff;">"{subject}"</strong> and our team will get back to you within <strong style="color:#00bfff;">24-48 hours</strong>.</p>
            <div style="background:rgba(0,191,255,0.08);border-radius:10px;padding:20px;margin:24px 0;text-align:center;">
              <p style="color:#aaa;margin:0 0 6px;font-size:0.85rem;">NEED URGENT HELP?</p>
              <p style="color:#fff;margin:0;">support@vishalsales.com</p>
              <p style="color:#fff;margin:4px 0 0;">+91 98765 43210</p>
            </div>
            <div style="text-align:center;">
              <a href="http://localhost:5500/frontend/index.html" style="background:linear-gradient(45deg,#00bfff,#0066cc);color:#fff;padding:12px 28px;border-radius:50px;text-decoration:none;font-weight:bold;">Continue Shopping</a>
            </div>
          </div>
          <div style="background:#111;padding:14px;text-align:center;color:#555;font-size:0.8rem;">
            &copy; 2025 VISHKART. All rights reserved.
          </div>
        </div>
        """
        send_email(email, "We received your message - VISHKART", html)
    except Exception as e:
        print(f"[Email] Failed to send contact confirmation to {email}: {e}")


if __name__ == "__main__":
    test_connection()
