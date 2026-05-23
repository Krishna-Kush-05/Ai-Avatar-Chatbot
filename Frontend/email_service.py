import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime
import logging

# Set up logging for email service
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("EmailService")

def send_onboarding_email(recipient_email, inviter_name, inviter_institution, registration_url):
    """
    Composes and sends an onboarding invitation email to a student.
    If SMTP_SERVER environment variable is not configured, it defaults to Mock Mode
    and writes the email as an HTML file in 'sent_emails/' for local review.
    """
    # Load configuration from environment variables
    smtp_server = os.environ.get("SMTP_SERVER", "").strip()
    smtp_port = int(os.environ.get("SMTP_PORT", "587"))
    smtp_username = os.environ.get("SMTP_USERNAME", "").strip()
    smtp_password = os.environ.get("SMTP_PASSWORD", "").strip()
    smtp_use_tls = os.environ.get("SMTP_USE_TLS", "True").strip().lower() in ("true", "1", "yes")
    default_sender = os.environ.get("MAIL_DEFAULT_SENDER", "noreply@ai-avatar-chatbot.com").strip()

    subject = f"Invitation to join AI Avatar Chatbot classroom"
    
    # Format institution name if present
    institution_str = f" at {inviter_institution}" if inviter_institution else ""

    # Beautiful CSS-styled premium HTML email body
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Welcome to AI Avatar Chatbot</title>
        <style>
            body {{
                font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
                background-color: #f3f4f6;
                margin: 0;
                padding: 0;
                -webkit-font-smoothing: antialiased;
            }}
            .container {{
                max-width: 600px;
                margin: 40px auto;
                background-color: #ffffff;
                border-radius: 16px;
                overflow: hidden;
                box-shadow: 0 4px 20px rgba(0, 0, 0, 0.05);
                border: 1px solid #e5e7eb;
            }}
            .header {{
                background: linear-gradient(135deg, #10b981 0%, #059669 100%);
                padding: 40px 30px;
                text-align: center;
                color: #ffffff;
            }}
            .logo-text {{
                font-size: 24px;
                font-weight: 800;
                letter-spacing: -0.03em;
                margin: 0 0 10px 0;
            }}
            .subtitle {{
                font-size: 16px;
                opacity: 0.9;
                margin: 0;
            }}
            .content {{
                padding: 40px 30px;
                color: #374151;
                line-height: 1.6;
            }}
            .greeting {{
                font-size: 18px;
                font-weight: 700;
                margin-top: 0;
                margin-bottom: 20px;
                color: #111827;
            }}
            .inviter-box {{
                background-color: #f0fdf4;
                border-left: 4px solid #10b981;
                padding: 15px 20px;
                border-radius: 4px 8px 8px 4px;
                margin-bottom: 30px;
                font-weight: 500;
                color: #065f46;
            }}
            .features {{
                display: grid;
                gap: 15px;
                margin-bottom: 35px;
            }}
            .feature-item {{
                display: flex;
                align-items: flex-start;
                gap: 12px;
                background-color: #fafafa;
                padding: 12px 16px;
                border-radius: 8px;
                border: 1px solid #f3f4f6;
            }}
            .feature-icon {{
                font-size: 20px;
                flex-shrink: 0;
            }}
            .feature-text strong {{
                color: #111827;
            }}
            .cta-container {{
                text-align: center;
                margin: 35px 0;
            }}
            .btn-primary {{
                display: inline-block;
                padding: 14px 30px;
                background: linear-gradient(135deg, #10b981 0%, #059669 100%);
                color: #ffffff !important;
                text-decoration: none;
                border-radius: 10px;
                font-weight: 600;
                font-size: 16px;
                box-shadow: 0 4px 14px rgba(16, 185, 129, 0.3);
                transition: transform 0.2s, box-shadow 0.2s;
            }}
            .footer {{
                background-color: #f9fafb;
                padding: 20px 30px;
                text-align: center;
                font-size: 12px;
                color: #9ca3af;
                border-top: 1px solid #f3f4f6;
            }}
            .footer a {{
                color: #10b981;
                text-decoration: none;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <div class="logo-text">AI AVATAR CHATBOT</div>
                <p class="subtitle">Classroom Learning Platform</p>
            </div>
            
            <div class="content">
                <p class="greeting">Hello!</p>
                
                <div class="inviter-box">
                    <strong>{inviter_name}</strong> has invited you to join their AI Avatar Chatbot classroom{institution_str} as a Student.
                </div>
                
                <p>Once you register, you will get access to:</p>
                
                <div class="features">
                    <div class="feature-item">
                        <span class="feature-icon">🤖</span>
                        <div class="feature-text">
                            <strong>Interactive AI Avatars:</strong> Engage with customized chatbot avatars built by your teacher specifically for your course material.
                        </div>
                    </div>
                    <div class="feature-item">
                        <span class="feature-icon">🎙️</span>
                        <div class="feature-text">
                            <strong>Speech & Audio capabilities:</strong> Speak directly to your avatars and listen to high-quality audio responses.
                        </div>
                    </div>
                    <div class="feature-item">
                        <span class="feature-icon">📁</span>
                        <div class="feature-text">
                            <strong>Shared Knowledge Hub:</strong> Study uploaded documents, websites, and reference materials curated for your learning.
                        </div>
                    </div>
                </div>
                
                <p>Click the button below to accept your invitation, set up your account password, and get started:</p>
                
                <div class="cta-container">
                    <a href="{registration_url}" class="btn-primary">Register & Join Classroom</a>
                </div>
                
                <p>Please register using your email address: <strong>{recipient_email}</strong></p>
            </div>
            
            <div class="footer">
                <p>If you did not expect this invitation, you can safely ignore this email.</p>
                <p>&copy; {datetime.now().year} AI Avatar Chatbot. All rights reserved.</p>
            </div>
        </div>
    </body>
    </html>
    """

    # --- Fallback / Mock Mode ---
    if not smtp_server:
        logger.info("SMTP_SERVER environment variable not found. Entering Mock Mode.")
        # Ensure target folder exists
        sent_emails_dir = os.path.join(os.path.dirname(__file__), "sent_emails")
        os.makedirs(sent_emails_dir, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_email = recipient_email.replace("@", "_at_").replace(".", "_")
        filename = f"invite_{safe_email}_{timestamp}.html"
        filepath = os.path.join(sent_emails_dir, filename)
        
        # Write the HTML content to a file
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(html_content)
            
        logger.info(f"[MOCK EMAIL] Saved student invitation for '{recipient_email}' to: {filepath}")
        print(f"\n[EMAIL MOCK SERVICE] Saved invitation HTML locally to preview: file:///{filepath.replace(os.sep, '/')}\n")
        return True

    # --- Live Mode using python standard smtplib ---
    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = default_sender
        msg["To"] = recipient_email

        # Plain text version for non-HTML email clients
        text_content = f"Welcome! {inviter_name} has invited you to join their AI Avatar Chatbot classroom{institution_str}.\n\nRegister using the link: {registration_url}"
        
        msg.attach(MIMEText(text_content, "plain"))
        msg.attach(MIMEText(html_content, "html"))

        # Setup SMTP Connection
        if smtp_use_tls:
            server = smtplib.SMTP(smtp_server, smtp_port, timeout=15)
            server.ehlo()
            server.starttls()
            server.ehlo()
        else:
            # SSL or plain port
            server = smtplib.SMTP_SSL(smtp_server, smtp_port, timeout=15)

        if smtp_username and smtp_password:
            server.login(smtp_username, smtp_password)

        server.sendmail(default_sender, recipient_email, msg.as_string())
        server.quit()
        logger.info(f"Successfully sent invitation email to {recipient_email} via SMTP server {smtp_server}")
        return True
    except Exception as e:
        logger.error(f"Failed to send email to {recipient_email} via SMTP: {str(e)}")
        # Raise or return False so caller can handle gracefully
        return False
