import aiosmtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from loguru import logger
import time
from app.config import settings


class EmailService:
    def __init__(self):
        self.smtp_config = {
            "hostname": settings.SMTP_HOST,
            "port": settings.SMTP_PORT,
            "username": settings.SMTP_USER,
            "password": settings.SMTP_PASSWORD,
            "use_tls": True,
        }

        # Validate configuration
        if not all([settings.SMTP_HOST, settings.SMTP_USER, settings.SMTP_PASSWORD]):
            logger.warning(
                "Email service configured partially - emails may not be sent"
            )
        else:
            logger.info(f"Email service configured for {settings.SMTP_HOST}")

        logger.debug(f"SMTP config: {settings.SMTP_HOST}:{settings.SMTP_PORT}")

    async def send_notification(self, contact_data: dict, ai_analysis: dict = None):
        """Send email notification to owner"""
        logger.info(f"Preparing notification email for {settings.SMTP_TO}")

        try:
            msg = MIMEMultipart("alternative")
            msg["From"] = settings.SMTP_FROM
            msg["To"] = settings.SMTP_TO
            msg["Subject"] = (
                f"[Priority: {ai_analysis.get('priority', 'medium').upper()}] New Contact from {contact_data['name']}"
            )

            # HTML version
            html = self._build_notification_html(contact_data, ai_analysis)
            msg.attach(MIMEText(html, "html"))

            # Send email
            start_time = time.time()
            await aiosmtplib.send(msg, **self.smtp_config)
            duration = time.time() - start_time

            logger.info(
                f"Notification email sent in {duration:.2f}s to {settings.SMTP_TO}"
            )

        except Exception as e:
            logger.exception(f"Failed to send notification email: {str(e)}")
            raise

    async def send_confirmation(self, contact_data: dict):
        """Send confirmation email to the user"""
        logger.info(f"Preparing confirmation email for {contact_data['email']}")

        try:
            msg = MIMEMultipart("alternative")
            msg["From"] = settings.SMTP_FROM
            msg["To"] = contact_data["email"]
            msg["Subject"] = "Thank you for your inquiry"

            # HTML version
            html = self._build_confirmation_html(contact_data)
            msg.attach(MIMEText(html, "html"))

            # Send email
            start_time = time.time()
            await aiosmtplib.send(msg, **self.smtp_config)
            duration = time.time() - start_time

            logger.success(
                f"Confirmation email sent in {duration:.2f}s to {contact_data['email']}"
            )

        except Exception as e:
            logger.exception(f"Failed to send confirmation email: {str(e)}")
            raise

    def _build_notification_html(
        self, contact_data: dict, ai_analysis: dict = None
    ) -> str:
        """Build HTML for notification email"""
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: #f8f9fa; padding: 20px; border-radius: 5px; }}
                .info {{ margin: 20px 0; }}
                .info-item {{ margin: 10px 0; }}
                .label {{ font-weight: bold; color: #666; }}
                .ai-analysis {{ background: #e3f2fd; padding: 15px; border-radius: 5px; margin-top: 20px; }}
                .priority-high {{ color: #d32f2f; }}
                .priority-medium {{ color: #f57c00; }}
                .priority-low {{ color: #388e3c; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h2>New Contact Request</h2>
                </div>
                
                <div class="info">
                    <div class="info-item">
                        <span class="label">From:</span> {contact_data['name']}
                    </div>
                    <div class="info-item">
                        <span class="label">Email:</span> {contact_data['email']}
                    </div>
                    <div class="info-item">
                        <span class="label">Phone:</span> {contact_data['phone']}
                    </div>
                    <div class="info-item">
                        <span class="label">Comment:</span> {contact_data.get('comment', 'No comment')}
                    </div>
                </div>
        """

        if ai_analysis:
            priority_class = f"priority-{ai_analysis.get('priority', 'medium')}"
            html += f"""
                <div class="ai-analysis">
                    <h3>🤖 AI Analysis</h3>
                    <div class="info-item">
                        <span class="label">Sentiment:</span> {ai_analysis.get('sentiment', 'N/A')}
                    </div>
                    <div class="info-item">
                        <span class="label">Priority:</span> 
                        <span class="{priority_class}">{ai_analysis.get('priority', 'N/A').upper()}</span>
                    </div>
                    <div class="info-item">
                        <span class="label">Category:</span> {ai_analysis.get('category', 'N/A')}
                    </div>
                    <div class="info-item">
                        <span class="label">Suggested Reply:</span><br>
                        {ai_analysis.get('auto_reply_suggestion', 'N/A')}
                    </div>
                </div>
            """

        html += """
            </div>
        </body>
        </html>
        """

        return html

    def _build_confirmation_html(self, contact_data: dict) -> str:
        """Build HTML for confirmation email"""
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: #4CAF50; color: white; padding: 20px; border-radius: 5px; }}
                .content {{ margin: 20px 0; }}
                .reference {{ background: #f8f9fa; padding: 15px; border-radius: 5px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h2>Thank you for contacting us!</h2>
                </div>
                
                <div class="content">
                    <p>Dear {contact_data['name']},</p>
                    <p>We have received your inquiry and will get back to you within 24 hours.</p>
                </div>
                
                <div class="reference">
                    <h3>Your message details:</h3>
                    <p><strong>Phone:</strong> {contact_data['phone']}</p>
                    <p><strong>Message:</strong> {contact_data.get('comment', 'No comment provided')}</p>
                </div>
                
                <p>Best regards,<br>Developer Team</p>
            </div>
        </body>
        </html>
        """
