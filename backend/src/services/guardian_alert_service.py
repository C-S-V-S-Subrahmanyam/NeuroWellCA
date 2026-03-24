"""
Guardian alert service using Twilio WhatsApp for crisis notifications.
"""
from datetime import datetime, timedelta, timezone
import logging
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from twilio.rest import Client

from src.models.models import User, CrisisLog, GuardianAlert
from src.utils.config import settings

logger = logging.getLogger(__name__)


class GuardianAlertService:
    """Send crisis alerts to guardian contacts with cooldown protection."""

    def __init__(self) -> None:
        self._client: Optional[Client] = None

    def _client_or_none(self) -> Optional[Client]:
        if not settings.TWILIO_ACCOUNT_SID or not settings.TWILIO_AUTH_TOKEN or not settings.TWILIO_WHATSAPP_FROM:
            return None
        if self._client is None:
            self._client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
        return self._client

    async def _is_cooldown_active(self, db: AsyncSession, user_id: int) -> bool:
        cutoff = datetime.now(timezone.utc) - timedelta(hours=settings.GUARDIAN_ALERT_COOLDOWN_HOURS)
        result = await db.execute(
            select(GuardianAlert)
            .where(GuardianAlert.user_id == user_id, GuardianAlert.created_at >= cutoff)
            .order_by(GuardianAlert.created_at.desc())
            .limit(1)
        )
        return result.scalar_one_or_none() is not None

    async def send_if_needed(
        self,
        db: AsyncSession,
        user: User,
        message_text: str,
        crisis_score: float,
        keywords: list[str],
    ) -> dict:
        """Send guardian WhatsApp alert if crisis and contact are configured."""
        if not user.guardian_contact:
            return {"sent": False, "reason": "guardian_contact_missing"}

        if await self._is_cooldown_active(db, user.id):
            return {"sent": False, "reason": "cooldown_active"}

        action_taken = "resource_provided"

        crisis_log = CrisisLog(
            user_id=user.id,
            message_text=message_text,
            crisis_score=int(crisis_score),
            keywords_detected=", ".join(keywords),
            action_taken=action_taken,
            resolved=False,
        )
        db.add(crisis_log)
        await db.flush()

        guardian_to = user.guardian_contact.strip()
        if not guardian_to.startswith("whatsapp:"):
            guardian_to = f"whatsapp:{guardian_to}"

        body = (
            f"NeuroWell Safety Alert\n"
            f"User: {user.username}\n"
            f"A high-risk message was detected and support resources were shown.\n"
            f"Please check in with them immediately.\n"
            f"Timestamp (UTC): {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')}"
        )

        alert = GuardianAlert(
            user_id=user.id,
            crisis_log_id=crisis_log.id,
            guardian_contact=user.guardian_contact,
            alert_sent=False,
            alert_method="whatsapp",
            message_sent=body,
        )
        db.add(alert)
        await db.flush()

        client = self._client_or_none()
        if client is None:
            logger.warning("Twilio credentials missing; guardian alert skipped")
            crisis_log.action_taken = "resource_provided"
            return {"sent": False, "reason": "twilio_not_configured"}

        try:
            twilio_message = client.messages.create(
                body=body,
                from_=settings.TWILIO_WHATSAPP_FROM,
                to=guardian_to,
            )
            alert.alert_sent = True
            alert.response_received = twilio_message.sid
            crisis_log.action_taken = "guardian_alerted"
            logger.warning("Guardian WhatsApp alert sent for user %s", user.id)
            return {"sent": True, "reason": "ok", "sid": twilio_message.sid}
        except Exception as exc:
            logger.error("Failed to send guardian WhatsApp alert: %s", exc)
            crisis_log.action_taken = "resource_provided"
            alert.response_received = f"error: {exc}"
            return {"sent": False, "reason": "send_failed"}


guardian_alert_service = GuardianAlertService()
