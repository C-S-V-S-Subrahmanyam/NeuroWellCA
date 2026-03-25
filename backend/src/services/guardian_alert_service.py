"""
Guardian alert service using SMTP email for crisis notifications.
"""
from datetime import datetime, timedelta, timezone
from email.message import EmailMessage
import logging
import smtplib
from pathlib import Path

from dotenv import dotenv_values
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.models import User, CrisisLog, GuardianAlert
from src.utils.config import settings

logger = logging.getLogger(__name__)


class GuardianAlertService:
    """Send crisis alerts to guardian contacts with cooldown protection."""

    def _resolve_smtp_config(self) -> dict:
        host = (settings.SMTP_HOST or "").strip()
        user = (settings.SMTP_USER or "").strip()
        password = settings.SMTP_PASSWORD or ""
        from_email = (settings.SMTP_FROM_EMAIL or "").strip()
        port = int(settings.SMTP_PORT)
        use_tls = bool(settings.SMTP_USE_TLS)

        if host and user and password:
            return {
                "host": host,
                "port": port,
                "user": user,
                "password": password,
                "from_email": from_email,
                "use_tls": use_tls,
            }

        this_file = Path(__file__).resolve()
        env_candidates = [this_file.parents[3] / ".env", this_file.parents[2] / ".env"]
        for env_path in env_candidates:
            if not env_path.exists():
                continue
            vals = dotenv_values(env_path)
            host = host or (vals.get("SMTP_HOST") or "").strip()
            user = user or (vals.get("SMTP_USER") or "").strip()
            password = password or (vals.get("SMTP_PASSWORD") or "")
            from_email = from_email or (vals.get("SMTP_FROM_EMAIL") or "").strip()
            if not port and vals.get("SMTP_PORT"):
                port = int(vals.get("SMTP_PORT"))
            if vals.get("SMTP_USE_TLS") is not None:
                use_tls = str(vals.get("SMTP_USE_TLS")).lower() in {"1", "true", "yes", "on"}

        return {
            "host": host,
            "port": port,
            "user": user,
            "password": password,
            "from_email": from_email,
            "use_tls": use_tls,
        }

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

        smtp_cfg = self._resolve_smtp_config()
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

        body = (
            f"🤖 NeuroWell Crisis Alert\n\n"
            f"👤 User: {user.username}\n"
            f"📈 Crisis score: {int(crisis_score)}\n"
            f"🔎 Detected keywords: {', '.join(keywords) if keywords else 'None'}\n\n"
            f"⚠️ A high-risk message was detected and support resources were shown.\n"
            f"🙏 Please check in with them immediately.\n"
            f"🕒 Timestamp (UTC): {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')}\n\n"
            f"💙 This alert was sent by NeuroWell chatbot safety monitor."
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
            email = EmailMessage()
            email["Subject"] = "🤖 NeuroWell Crisis Alert"
            email["From"] = smtp_cfg["from_email"] or smtp_cfg["user"]
            email["To"] = guardian_email
            email.set_content(body)

            with smtplib.SMTP(smtp_cfg["host"], smtp_cfg["port"], timeout=20) as smtp:
                if smtp_cfg["use_tls"]:
                    smtp.starttls()
                smtp.login(smtp_cfg["user"], smtp_cfg["password"])
                smtp.send_message(email)

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
