from mistralai.client import Mistral
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
)
from loguru import logger
import json
import time
from app.config import settings
from app.models.contact import ContactRequest, AIAnalysis


class AIService:
    def __init__(self):
        self.client = None
        self.model = settings.MISTRAL_MODEL

        if settings.mistral_available:
            try:
                self.client = Mistral(api_key=settings.MISTRAL_API_KEY)
                logger.info(f"Mistral AI client initialized successfully")
                logger.info(f"Using model: {self.model}")
            except Exception as e:
                logger.error(f"Failed to initialize Mistral client: {str(e)}")
                logger.warning("AI features will use fallback mode")
        else:
            logger.warning(
                "Mistral API key not configured - AI features will use fallback"
            )
            logger.info("Get your free API key at: https://console.mistral.ai/")

    async def analyze_contact(self, contact: ContactRequest) -> AIAnalysis:
        """Analyze contact request using Mistral AI"""
        logger.info(f"Starting AI analysis for contact from {contact.email}")

        if not self.client:
            logger.warning("AI analysis skipped - Mistral client not available")
            return self._get_fallback_analysis()

        # Build messages for Mistral
        messages = self._build_analysis_messages(contact)
        logger.debug(f"Built analysis messages: {len(messages)} messages")

        try:
            start_time = time.time()
            analysis = await self._call_mistral_with_retry(messages)
            duration = time.time() - start_time

            logger.info(
                f"AI analysis completed in {duration:.2f}s | "
                f"Sentiment: {analysis.get('sentiment')} | "
                f"Priority: {analysis.get('priority')} | "
                f"Category: {analysis.get('category')}"
            )

            return AIAnalysis(**analysis)

        except Exception as e:
            logger.exception(f"AI analysis failed: {str(e)}")
            logger.info("Falling back to default analysis")
            return self._get_fallback_analysis()

    async def generate_smart_reply(
        self, contact: ContactRequest, analysis: AIAnalysis
    ) -> str:
        """Generate a smart reply based on contact and analysis"""
        logger.info(f"Generating smart reply for {contact.email}")

        if not self.client:
            logger.warning(
                "Smart reply generation skipped - Mistral client not available"
            )
            return self._get_fallback_reply(contact)

        messages = self._build_reply_messages(contact, analysis)

        try:
            start_time = time.time()
            reply = await self._call_mistral_chat(messages, max_tokens=200)
            duration = time.time() - start_time

            logger.info(f"Smart reply generated in {duration:.2f}s")
            logger.debug(f"Generated reply: {reply[:100]}...")

            return reply

        except Exception as e:
            logger.exception(f"Smart reply generation failed: {str(e)}")
            return self._get_fallback_reply(contact)

    async def classify_urgency(self, contact: ContactRequest) -> dict:
        """Additional AI function: classify urgency and suggest response time"""
        logger.info(f"Classifying urgency for {contact.email}")

        if not self.client:
            return {"urgency": "medium", "response_time": "24 hours"}

        messages = [
            {
                "role": "system",
                "content": "You are an AI assistant that classifies the urgency of client inquiries.",
            },
            {
                "role": "user",
                "content": f"""
                Classify the urgency of this inquiry:
                
                Client: {contact.name}
                Comment: {contact.comment or 'No comment'}
                
                Return JSON with:
                - urgency: "low", "medium", "high", or "critical"
                - response_time: suggested response time (e.g., "24 hours", "4 hours", "1 hour")
                - reason: brief explanation
                
                Respond ONLY with valid JSON.
                """,
            },
        ]

        try:
            result = await self._call_mistral_chat(messages, max_tokens=100)
            urgency_data = json.loads(result)
            logger.info(f"Urgency classified: {urgency_data.get('urgency')}")
            return urgency_data
        except Exception as e:
            logger.error(f"Urgency classification failed: {str(e)}")
            return {
                "urgency": "medium",
                "response_time": "24 hours",
                "reason": "fallback",
            }

    def _build_analysis_messages(self, contact: ContactRequest) -> list:
        """Build messages for contact analysis"""
        system_prompt = """You are an AI assistant that analyzes client inquiries for a software developer's landing page.
        Analyze each inquiry and provide structured JSON output.
        
        Categories can be:
        - web_development: Website/web app development requests
        - mobile_development: Mobile app development requests
        - consulting: Technical consulting or advice
        - job_opportunity: Job offers or career opportunities
        - partnership: Business partnerships or collaborations
        - support: Technical support requests
        - general: General inquiries
        
        Always respond with valid JSON only, no markdown formatting."""

        user_prompt = f"""Analyze this contact request from a potential client:

        Name: {contact.name}
        Email: {contact.email}
        Phone: {contact.phone}
        Comment: {contact.comment or 'No comment provided'}

        Provide analysis in JSON format with these exact fields:
        - sentiment: "positive", "neutral", or "negative"
        - priority: "high", "medium", or "low"
        - category: one of the categories listed above
        - auto_reply_suggestion: personalized reply text in professional tone

        Example response:
        {{"sentiment": "positive", "priority": "high", "category": "web_development", "auto_reply_suggestion": "Thank you for reaching out about your web development project..."}}"""

        return [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

    def _build_reply_messages(
        self, contact: ContactRequest, analysis: AIAnalysis
    ) -> list:
        """Build messages for smart reply generation"""
        system_prompt = """You are a professional software developer responding to client inquiries.
        Write personalized, professional responses that:
        1. Address the client by name
        2. Reference their specific inquiry
        3. Set clear expectations about next steps
        4. Maintain a friendly but professional tone
        5. Are concise (2-3 sentences)"""

        user_prompt = f"""Write a personalized reply for this client:

        Client: {contact.name}
        Category: {analysis.category}
        Sentiment: {analysis.sentiment}
        Priority: {analysis.priority}
        Comment: {contact.comment or 'No specific comment'}
        
        Generate a professional response."""

        return [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((Exception,)),
        before_sleep=lambda retry_state: logger.warning(
            f"Retrying Mistral API call (attempt {retry_state.attempt_number})"
        ),
        reraise=True,
    )
    async def _call_mistral_with_retry(self, messages: list) -> dict:
        """Call Mistral API with retry logic for JSON responses"""
        logger.debug(f"Calling Mistral API for analysis")

        try:
            # Use Mistral's chat completion
            response = await self.client.chat.complete_async(
                model=self.model,
                messages=messages,
                temperature=0.3,
                max_tokens=300,
                response_format={"type": "json_object"},  # Mistral supports JSON mode
            )

            content = response.choices[0].message.content
            logger.debug(f"Received Mistral response: {content[:200]}...")

            # Parse JSON response
            try:
                result = json.loads(content)
                logger.debug("Successfully parsed Mistral response as JSON")
                return result
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse Mistral response as JSON: {str(e)}")
                logger.error(f"Raw response: {content}")
                # Try to extract JSON from response
                return self._extract_json_from_response(content)

        except Exception as e:
            logger.error(f"Mistral API call failed: {str(e)}")
            raise

    async def _call_mistral_chat(self, messages: list, max_tokens: int = 200) -> str:
        """Call Mistral API for chat responses"""
        logger.debug(f"Calling Mistral API for chat completion")

        try:
            response = await self.client.chat.complete_async(
                model=self.model,
                messages=messages,
                temperature=0.7,
                max_tokens=max_tokens,
            )

            content = response.choices[0].message.content
            logger.debug(f"Received chat response: {content[:100]}...")

            return content.strip()

        except Exception as e:
            logger.error(f"Mistral chat call failed: {str(e)}")
            raise

    def _extract_json_from_response(self, text: str) -> dict:
        """Try to extract JSON from text response"""
        import re

        # Try to find JSON object in the text
        json_match = re.search(r"\{[^}]+\}", text)
        if json_match:
            try:
                return json.loads(json_match.group())
            except json.JSONDecodeError:
                pass

        # If all else fails, create a basic response
        logger.warning("Could not extract JSON, using basic analysis")
        return {
            "sentiment": "neutral",
            "priority": "medium",
            "category": "general",
            "auto_reply_suggestion": "Thank you for your inquiry. We will get back to you soon.",
        }

    def _get_fallback_analysis(self) -> AIAnalysis:
        """Return default analysis when AI is unavailable"""
        logger.info("Generating fallback analysis")

        return AIAnalysis(
            sentiment="neutral",
            priority="medium",
            category="general",
            auto_reply_suggestion="Thank you for your inquiry. We've received your message and will get back to you within 24 hours.",
        )

    def _get_fallback_reply(self, contact: ContactRequest) -> str:
        """Return default reply when AI is unavailable"""
        return f"Dear {contact.name},\n\nThank you for reaching out! I've received your message and will review it shortly. I typically respond within 24 hours.\n\nBest regards,\nDeveloper"
