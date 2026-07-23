from loguru import logger
from typing import Dict, Any
import asyncio
from datetime import datetime
from app.models.contact import ContactRequest
from .ai_service import AIService
from .email_service import EmailService
from app.utils.file_storage import FileStorage


class ContactService:
    def __init__(self):
        self.ai_service = AIService()
        self.email_service = EmailService()
        self.file_storage = FileStorage()
        logger.info("ContactService initialized with Mistral AI")

    async def process_contact(self, contact: ContactRequest) -> Dict[str, Any]:
        """Process contact form submission with enhanced AI features"""

        logger.info(f"Processing contact from {contact.name} <{contact.email}>")

        # Prepare contact data
        contact_data = contact.model_dump()
        logger.debug(f"Contact data prepared: {contact_data['name']}")

        # AI Analysis - основная функция
        logger.info("Starting AI analysis with Mistral")
        ai_analysis = await self.ai_service.analyze_contact(contact)
        ai_analysis_dict = ai_analysis.model_dump()

        # Дополнительные AI функции
        logger.info("Running additional AI features")

        # 1. Smart reply generation
        smart_reply = await self.ai_service.generate_smart_reply(contact, ai_analysis)

        # 2. Urgency classification
        urgency_info = await self.ai_service.classify_urgency(contact)

        logger.info(
            f"AI Analysis complete - "
            f"Sentiment: {ai_analysis.sentiment}, "
            f"Priority: {ai_analysis.priority}, "
            f"Category: {ai_analysis.category}, "
            f"Urgency: {urgency_info.get('urgency', 'unknown')}"
        )

        # Update metrics
        logger.debug("Updating metrics with AI analysis data")
        await self.file_storage.update_metrics(
            {
                "sentiment": ai_analysis.sentiment,
                "category": ai_analysis.category,
                "urgency": urgency_info.get("urgency", "medium"),
                "success": True,
            }
        )

        # Send emails asynchronously
        logger.info("Sending email notifications with AI-enhanced content")

        # Update analysis with smart reply
        ai_analysis_dict["smart_reply"] = smart_reply
        ai_analysis_dict["urgency_info"] = urgency_info

        # Create tasks for email sending
        notification_task = asyncio.create_task(
            self._send_notification_safe(contact_data, ai_analysis_dict)
        )
        confirmation_task = asyncio.create_task(
            self._send_confirmation_safe(contact_data)
        )

        logger.debug("Email tasks created and running asynchronously")

        return {
            "success": True,
            "message": "Thank you for your inquiry. We will contact you soon!",
            "data": contact_data,
            "ai_analysis": ai_analysis_dict,
            "timestamp": datetime.utcnow().isoformat(),
        }

    async def _send_notification_safe(self, contact_data: dict, ai_analysis: dict):
        """Send notification email with error handling"""
        try:
            logger.info(f"Sending AI-enhanced notification to owner")
            await self.email_service.send_notification(contact_data, ai_analysis)
            logger.success("Notification email sent successfully")
        except Exception as e:
            logger.exception(f"Failed to send notification email: {str(e)}")

    async def _send_confirmation_safe(self, contact_data: dict):
        """Send confirmation email with error handling"""
        try:
            logger.info(f"Sending confirmation email to {contact_data['email']}")
            await self.email_service.send_confirmation(contact_data)
            logger.success(f"Confirmation email sent to {contact_data['email']}")
        except Exception as e:
            logger.exception(f"Failed to send confirmation email: {str(e)}")
