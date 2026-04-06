"""
Shared email service with blue-gradient HTML templates.
"""
from datetime import datetime, timezone
from email.message import EmailMessage
import smtplib
from pathlib import Path
from typing import Tuple

from dotenv import dotenv_values

from src.utils.config import settings


def resolve_smtp_config() -> dict:
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
        if vals.get("SMTP_PORT"):
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


def build_blue_gradient_email_html(title: str, subtitle: str, content_html: str) -> str:
    return f"""
<!DOCTYPE html>
<html>
<head>
  <meta charset=\"UTF-8\" />
  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\" />
</head>
<body style=\"margin:0;padding:0;background:#eef6ff;font-family:Arial,sans-serif;color:#0f172a;\">
  <table role=\"presentation\" width=\"100%\" cellspacing=\"0\" cellpadding=\"0\" style=\"padding:24px 12px;\">
    <tr>
      <td align=\"center\">
        <table role=\"presentation\" width=\"100%\" cellspacing=\"0\" cellpadding=\"0\" style=\"max-width:620px;background:#ffffff;border-radius:18px;overflow:hidden;border:1px solid #dbeafe;\">
          <tr>
            <td style=\"background:linear-gradient(135deg,#1d4ed8 0%,#2563eb 45%,#38bdf8 100%);padding:28px 26px;color:#ffffff;\">
              <h1 style=\"margin:0;font-size:24px;line-height:1.3;\">{title}</h1>
              <p style=\"margin:8px 0 0;font-size:14px;opacity:.95;\">{subtitle}</p>
            </td>
          </tr>
          <tr>
            <td style=\"padding:24px 26px 10px;line-height:1.65;font-size:15px;\">
              {content_html}
            </td>
          </tr>
          <tr>
            <td style=\"padding:8px 26px 24px;color:#475569;font-size:12px;\">
              Sent by NeuroWell at {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}
            </td>
          </tr>
        </table>
      </td>
    </tr>
  </table>
</body>
</html>
"""


def send_email_with_template(
    to_email: str,
    subject: str,
    title: str,
    subtitle: str,
    content_html: str,
    plain_text: str,
) -> Tuple[bool, str]:
    smtp_cfg = resolve_smtp_config()
    if not smtp_cfg["host"] or not smtp_cfg["user"] or not smtp_cfg["password"]:
        return False, "smtp_not_configured"

    html = build_blue_gradient_email_html(title=title, subtitle=subtitle, content_html=content_html)

    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = smtp_cfg["from_email"] or smtp_cfg["user"]
    msg["To"] = to_email
    msg.set_content(plain_text)
    msg.add_alternative(html, subtype="html")

    try:
      with smtplib.SMTP(smtp_cfg["host"], smtp_cfg["port"], timeout=20) as smtp:
          if smtp_cfg["use_tls"]:
              smtp.starttls()
          smtp.login(smtp_cfg["user"], smtp_cfg["password"])
          smtp.send_message(msg)
      return True, "ok"
    except Exception:
      return False, "send_failed"
