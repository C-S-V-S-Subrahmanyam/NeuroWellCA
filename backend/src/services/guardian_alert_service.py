"""
Guardian alert service using SMTP email for crisis notifications.
"""
from datetime import datetime, timedelta, timezone
import logging
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.models import User, CrisisLog, GuardianAlert
from src.utils.config import settings
from src.services.email_service import resolve_smtp_config, send_email_with_template

logger = logging.getLogger(__name__)


class GuardianAlertService:
    """Send crisis alerts to guardian contacts with cooldown protection."""

    async def _is_cooldown_active(self, db: AsyncSession, user_id: int) -> bool:
        cutoff = datetime.now(timezone.utc) - timedelta(hours=settings.GUARDIAN_ALERT_COOLDOWN_HOURS)
        result = await db.execute(
            select(GuardianAlert)
            .where(
                GuardianAlert.user_id == user_id,
                GuardianAlert.created_at >= cutoff,
                GuardianAlert.alert_sent.is_(True),
            )
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
        """Send guardian email alert if crisis and contact are configured."""
        guardian_email = (user.guardian_email or "").strip()
        if not guardian_email:
            return {"sent": False, "reason": "guardian_email_missing"}

        smtp_cfg = resolve_smtp_config()
        if not smtp_cfg["host"] or not smtp_cfg["user"] or not smtp_cfg["password"]:
            return {"sent": False, "reason": "smtp_not_configured"}

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

        timestamp = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')
        body = (
            f"NeuroWell Crisis Alert\n\n"
            f"User: {user.username}\n"
            f"Crisis score: {int(crisis_score)}\n"
            f"Detected keywords: {', '.join(keywords) if keywords else 'None'}\n"
            f"Timestamp (UTC): {timestamp}\n\n"
            "A high-risk message was detected and support resources were shown.\n"
            "Please check in with them immediately."
        )

        alert = GuardianAlert(
            user_id=user.id,
            crisis_log_id=crisis_log.id,
            guardian_contact=guardian_email,
            alert_sent=False,
            alert_method="email",
            message_sent=body,
        )
        db.add(alert)
        await db.flush()

        try:
            content_html = (
                "<p style='margin:0 0 14px;'>A high-risk message was detected in NeuroWell and support resources were already shown to the user.</p>"
                f"<p style='margin:0 0 8px;'><strong>User:</strong> {user.username}</p>"
                f"<p style='margin:0 0 8px;'><strong>Crisis score:</strong> {int(crisis_score)}</p>"
                f"<p style='margin:0 0 8px;'><strong>Detected keywords:</strong> {', '.join(keywords) if keywords else 'None'}</p>"
                f"<p style='margin:0 0 12px;'><strong>Timestamp (UTC):</strong> {timestamp}</p>"
                "<p style='margin:0;color:#0f172a;'><strong>Please check in with them immediately.</strong></p>"
            )

            sent, reason = send_email_with_template(
                to_email=guardian_email,
                subject="NeuroWell Crisis Alert",
                title="Urgent Guardian Alert",
                subtitle="A crisis signal was detected",
                content_html=content_html,
                plain_text=body,
            )
            if not sent:
                raise RuntimeError(reason)

            alert.alert_sent = True
            alert.response_received = "smtp_sent"
            crisis_log.action_taken = "guardian_alerted"
            logger.warning("Guardian email alert sent for user %s", user.id)
            return {"sent": True, "reason": "ok", "provider": "smtp"}
        except Exception as exc:
            logger.error("Failed to send guardian email alert: %s", exc)
            crisis_log.action_taken = "resource_provided"
            alert.response_received = f"error: {exc}"
            return {"sent": False, "reason": "send_failed"}


guardian_alert_service = GuardianAlertService()
