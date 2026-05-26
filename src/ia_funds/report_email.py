from __future__ import annotations

import logging
import os
import smtplib
import ssl
from datetime import datetime
from email.message import EmailMessage
from email.utils import formatdate
from zoneinfo import ZoneInfo

import pandas as pd

from ia_funds.seg_fund_email_html import build_fund_analysis_email_html

log = logging.getLogger(__name__)


def build_summary_table(wide: pd.DataFrame) -> pd.DataFrame:
    meta = ["Funds", "Asset class", "Code"]
    date_cols = [c for c in wide.columns if c not in meta]
    if not date_cols:
        return wide[meta].copy()
    d_last = date_cols[-1]
    last = pd.to_numeric(wide[d_last], errors="coerce")
    out = wide[meta].copy()
    out["as_of"] = d_last
    out["last_nav"] = last
    if len(date_cols) >= 2:
        d_prev = date_cols[-2]
        prev = pd.to_numeric(wide[d_prev], errors="coerce")
        out["prior_nav"] = prev
        out["pct_vs_prior"] = (last / prev - 1.0).where(prev.notna() & (prev != 0))
        return out.sort_values("pct_vs_prior", ascending=False, na_position="last")
    return out.sort_values("last_nav", ascending=False, na_position="last")


def _data_as_of_label(wide: pd.DataFrame) -> str:
    meta = ["Funds", "Asset class", "Code"]
    date_cols = [c for c in wide.columns if c not in meta]
    if not date_cols:
        return "\u2014"
    return str(date_cols[-1])


def _report_dates_local() -> tuple[str, str]:
    """Human-readable date and YYYY-MM-DD in FUND_REPORT_TZ (matches seg-fund-scraper)."""
    tz_name = (os.environ.get("FUND_REPORT_TZ") or "America/Toronto").strip()
    tz = ZoneInfo(tz_name or "America/Toronto")
    now = datetime.now(tz)
    month = now.strftime("%B")
    human = f"{month} {now.day}, {now.year}"
    iso = now.strftime("%Y-%m-%d")
    return human, iso


def _parse_recipients(mail_to: str | None) -> list[str]:
    raw = (mail_to or "").strip()
    if not raw:
        raw = (os.environ.get("MAIL_TO") or os.environ.get("FUND_REPORT_RECIPIENTS") or "").strip()
    parts = raw.replace(";", ",").split(",")
    return [p.strip() for p in parts if p.strip()]


def _resolve_mail_from(mail_from: str | None) -> str:
    return (mail_from or os.environ.get("MAIL_FROM") or os.environ.get("SMTP_FROM") or "").strip()


def html_email_body(wide: pd.DataFrame, title: str | None = None) -> str:
    """Return the seg-fund-scraper-style HTML body (``title`` is ignored; kept for API compatibility)."""
    _ = title
    summary = build_summary_table(wide)
    return build_fund_analysis_email_html(summary, data_as_of=_data_as_of_label(wide))


def send_report_smtp(
    wide: pd.DataFrame,
    subject: str | None = None,
    *,
    mail_from: str | None = None,
    mail_to: str | None = None,
) -> None:
    """
    Send the fund HTML report by email (same structure as seg-fund-scraper ``send_fund_report_smtp.py``):

    multipart ``EmailMessage`` with a plain intro, HTML alternative, and a ``.html`` attachment
    named ``iA-Seg-Fund-Report-<YYYY-MM-DD>.html`` (date in ``FUND_REPORT_TZ``).

    Environment (in addition to existing ``MAIL_*`` / ``SMTP_*`` variables):

    - ``FUND_REPORT_RECIPIENTS`` — comma-separated To addresses (seg-fund-scraper name).
    - ``SMTP_FROM`` — From address if ``MAIL_FROM`` is unset.
    - ``FUND_REPORT_TZ`` — IANA zone for subject/attachment date (default ``America/Toronto``).
    - ``SMTP_SSL`` — if ``1``/``true``, use implicit TLS (``SMTP_SSL``), typical for port 465.
    """
    host = os.environ.get("SMTP_HOST", "localhost").strip()
    port_s = (os.environ.get("SMTP_PORT") or "587").strip()
    try:
        port = int(port_s)
    except ValueError as e:
        raise ValueError(f"Invalid SMTP_PORT: {port_s!r}") from e

    user = (os.environ.get("SMTP_USER") or "").strip()
    password = (os.environ.get("SMTP_PASSWORD") or "").strip()
    mail_from_r = _resolve_mail_from(mail_from)
    recipients = _parse_recipients(mail_to)

    if not mail_from_r or not recipients:
        raise ValueError(
            "Set MAIL_FROM and MAIL_TO (or FUND_REPORT_RECIPIENTS), or pass mail_from / mail_to. "
            "SMTP_FROM is accepted as a fallback for MAIL_FROM."
        )
    if bool(user) != bool(password):
        raise ValueError("SMTP_USER and SMTP_PASSWORD must both be set or both empty.")

    human_date, iso_date = _report_dates_local()
    if subject is None:
        subject = f"iA Seg Fund Report — {human_date}"

    intro = (
        f"Here is the iA Seg Fund Report for {human_date}\n\n"
        "If you do not see formatted tables below, enable HTML email or open the attached .html file."
    )

    summary = build_summary_table(wide)
    html_text = build_fund_analysis_email_html(summary, data_as_of=_data_as_of_label(wide))
    html_bytes = html_text.encode("utf-8")

    use_ssl = os.environ.get("SMTP_SSL", "").strip().lower() in ("1", "true", "yes", "on") or port == 465
    use_tls = os.environ.get("SMTP_TLS", "1") not in ("0", "false", "False")

    log.info(
        "Sending report email via SMTP %s:%s (SSL=%s STARTTLS=%s) to %d recipient(s)",
        host,
        port,
        use_ssl,
        use_tls and not use_ssl,
        len(recipients),
    )

    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = mail_from_r
    msg["To"] = ", ".join(recipients)
    msg["Date"] = formatdate(localtime=True)
    msg.set_content(intro, subtype="plain", charset="utf-8")
    msg.add_alternative(html_text, subtype="html", charset="utf-8")
    msg.add_attachment(
        html_bytes,
        maintype="text",
        subtype="html",
        filename=f"iA-Seg-Fund-Report-{iso_date}.html",
    )

    ctx = ssl.create_default_context()

    if use_ssl:
        with smtplib.SMTP_SSL(host, port, context=ctx, timeout=120) as smtp:
            if user:
                smtp.login(user, password)
            smtp.send_message(msg)
    else:
        with smtplib.SMTP(host, port, timeout=120) as smtp:
            smtp.ehlo()
            if use_tls and smtp.has_extn("starttls"):
                smtp.starttls(context=ctx)
                smtp.ehlo()
            if user:
                smtp.login(user, password)
            smtp.send_message(msg)

    log.info("Email sent to %s", ", ".join(recipients))
