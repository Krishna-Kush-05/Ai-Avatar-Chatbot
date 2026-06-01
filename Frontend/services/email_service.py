import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("EmailService")

def send_invitation_email(to_email, invite_link):
    """
    Sends a real SMTP email via smtp.gmail.com.
    Requires EMAIL_USER and EMAIL_PASS environment variables.
    """
    email_user = os.environ.get("EMAIL_USER", "").strip()
    email_pass = os.environ.get("EMAIL_PASS", "").strip()

    if not email_user or not email_pass:
        logger.error("Missing EMAIL_USER or EMAIL_PASS environment variables.")
        return False

    smtp_server = "smtp.gmail.com"
    smtp_port = 587

    subject = "You're Invited to AI Avatar Chatbot!"
    
    html_content = f"""
    <html>
      <body style="font-family: sans-serif; line-height: 1.6; color: #333;">
        <div style="max-width: 600px; margin: auto; padding: 20px; border: 1px solid #eee; border-radius: 8px;">
            <h2 style="color: #10b981;">Welcome to AI Avatar Chatbot!</h2>
            <p>You have been invited to join a classroom.</p>
            <p>Click the link below to accept your invitation, create your password, and begin interacting with AI avatars:</p>
            <p style="text-align: center; margin: 30px 0;">
                <a href="{invite_link}" style="background-color: #10b981; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; font-weight: bold;">Accept Invitation & Register</a>
            </p>
            <p>Or paste this link into your browser:<br>
            <a href="{invite_link}">{invite_link}</a></p>
            <hr style="border: none; border-top: 1px solid #eee; margin: 20px 0;">
            <p style="font-size: 0.8em; color: #777;">If you weren't expecting this invitation, you can safely ignore this email.</p>
        </div>
      </body>
    </html>
    """

    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = email_user
        msg["To"] = to_email

        # Fallback plain text
        text_content = f"You have been invited to join AI Avatar Chatbot!\nRegister here: {invite_link}"
        
        msg.attach(MIMEText(text_content, "plain"))
        msg.attach(MIMEText(html_content, "html"))

        # Setup SMTP Connection
        server = smtplib.SMTP(smtp_server, smtp_port, timeout=15)
        server.ehlo()
        server.starttls()
        server.ehlo()

        server.login(email_user, email_pass)
        server.sendmail(email_user, to_email, msg.as_string())
        server.quit()
        
        logger.info(f"Successfully sent invitation email to {to_email} via SMTP")
        return True
    except Exception as e:
        logger.error(f"Failed to send email to {to_email} via SMTP: {str(e)}")
        # Do not crash app, just return False
        return False
