from __future__ import annotations

import logging
import re
from pathlib import Path

import pandas as pd

from ia_funds.loader import wide_to_long

log = logging.getLogger(__name__)


def sanitize_ticker(code: str) -> str:
    """MetaStock tickers are safest as letters, digits, underscore."""
    code = str(code).strip()
    code = re.sub(r"[^A-Za-z0-9._-]", "_", code)
    return code[:50] if len(code) > 50 else code


def export_metastock_ascii(long: pd.DataFrame, dest: str | Path) -> Path:
    """
    Write a multi-symbol daily ASCII file suitable for MetaStock DownLoader conversion.

    Each row: TICKER, PER, DTYYYYMMDD, TIME, OPEN, HIGH, LOW, CLOSE, VOLUME, OPENINT
    NAV-only series uses OPEN=HIGH=LOW=CLOSE=NAV, VOLUME=0, OPENINT=0.
    Rows are grouped by ticker and sorted ascending by date (MetaStock requirement).
    """
    dest = Path(dest)
    dest.parent.mkdir(parents=True, exist_ok=True)

    log.debug("Writing MetaStock ASCII: %s (%d rows)", dest, len(long))
    df = long.copy()
    df = df.rename(columns={"Funds": "name", "Code": "code", "date": "dt", "nav": "close"})
    df["ticker"] = df["code"].map(sanitize_ticker)
    df["dt"] = pd.to_datetime(df["dt"])
    df = df.sort_values(["ticker", "dt"])

    lines: list[str] = []
    # Header compatible with MetaStock 13+ flexible DATE field
    lines.append("TICKER,PER,DATE,TIME,OPEN,HIGH,LOW,CLOSE,VOLUME,OPENINT")
    for _, row in df.iterrows():
        d = row["dt"]
        date_s = d.strftime("%Y%m%d")
        c = float(row["close"])
        vol = 0
        oi = 0
        t = row["ticker"]
        # four decimals typical for fund NAV
        price = f"{c:.4f}"
        lines.append(f"{t},D,{date_s},000000,{price},{price},{price},{price},{vol},{oi}")

    text = "\n".join(lines) + "\n"
    dest.write_text(text, encoding="utf-8")
    log.debug("export_metastock_ascii: wrote %d data lines", len(lines) - 1)
    return dest


def export_per_ticker_files(long: pd.DataFrame, out_dir: str | Path) -> list[Path]:
    """Write one ASCII file per Code (basename = ticker)."""
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    groups = list(long.groupby("Code"))
    log.info("Writing MetaStock per-ticker files under %s (%d tickers)", out_dir, len(groups))
    written: list[Path] = []
    for code, g in long.groupby("Code"):
        tick = sanitize_ticker(code)
        path = out_dir / f"{tick}.csv"
        export_metastock_ascii(g, path)
        written.append(path)
    log.info("Wrote %d MetaStock ASCII files", len(written))
    return written


def wide_csv_to_metastock(wide: pd.DataFrame, dest: str | Path) -> Path:
    log.debug("wide_csv_to_metastock: melting wide frame (%d rows)", len(wide))
    long = wide_to_long(wide)
    log.info("Writing combined MetaStock ASCII: %s (%d NAV rows)", dest, len(long))
    return export_metastock_ascii(long, dest)
