from __future__ import annotations

import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import formatdate

import pandas as pd

from ia_funds.loader import wide_to_long


def build_summary_table(wide: pd.DataFrame) -> pd.DataFrame:
    meta = ["Funds", "Asset class", "Code"]
    date_cols = [c for c in wide.columns if c not in meta]
    if not date_cols:
        return wide[meta].copy()
    d_last = date_cols[-1]
    out = wide[meta + [d_last]].rename(columns={d_last: "last_nav"})
    out.insert(3, "as_of", d_last)
    if len(date_cols) >= 2:
        d_prev = date_cols[-2]
        prev = wide[d_prev]
        last = wide[d_last]
        out["pct_vs_prior"] = (last / prev - 1.0).where(prev.notna() & (prev != 0))
    else:
        out["pct_vs_prior"] = pd.NA
    return out.sort_values("pct_vs_prior", ascending=False, na_position="last")


def html_email_body(wide: pd.DataFrame, title: str = "iA funds performance report") -> str:
    summary = build_summary_table(wide)
    long = wide_to_long(wide)
    last_date = str(long["date"].max().date()) if len(long) else ""

    top = summary.dropna(subset=["pct_vs_prior"]).head(10)
    bottom = summary.dropna(subset=["pct_vs_prior"]).tail(10).sort_values("pct_vs_prior")

    def df_to_html_fragment(df: pd.DataFrame) -> str:
        return df.to_html(index=False, float_format=lambda x: f"{x:.4f}" if isinstance(x, float) else str(x))

    parts = [
        f"<html><head><meta charset='utf-8'><title>{title}</title></head><body>",
        f"<h2>{title}</h2>",
        f"<p>As-of (latest column in file): <b>{last_date}</b></p>",
        "<h3>Top movers vs prior day</h3>",
        df_to_html_fragment(top),
        "<h3>Largest declines vs prior day</h3>",
        df_to_html_fragment(bottom),
        "<p><i>Generated from your wide-format NAV export.</i></p>",
        "</body></html>",
    ]
    return "\n".join(parts)


def send_report_smtp(
    wide: pd.DataFrame,
    subject: str,
    *,
    mail_from: str | None = None,
    mail_to: str | None = None,
) -> None:
    host = os.environ.get("SMTP_HOST", "localhost")
    port = int(os.environ.get("SMTP_PORT", "587"))
    user = os.environ.get("SMTP_USER")
    password = os.environ.get("SMTP_PASSWORD")
    mail_from = mail_from or os.environ.get("MAIL_FROM")
    mail_to = mail_to or os.environ.get("MAIL_TO")
    if not mail_from or not mail_to:
        raise ValueError("Set MAIL_FROM and MAIL_TO (or pass mail_from / mail_to).")

    use_tls = os.environ.get("SMTP_TLS", "1") not in ("0", "false", "False")

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = mail_from
    msg["To"] = mail_to
    msg["Date"] = formatdate(localtime=True)
    html_body = html_email_body(wide, title=subject)
    msg.attach(MIMEText(html_body, "html", "utf-8"))

    with smtplib.SMTP(host, port, timeout=60) as smtp:
        if use_tls:
            smtp.starttls()
        if user and password:
            smtp.login(user, password)
        smtp.sendmail(mail_from, [mail_to], msg.as_string())
