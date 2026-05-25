from __future__ import annotations

import sys
import time
from datetime import date, datetime, timedelta
from typing import Any, Callable, Literal

import pandas as pd
import requests

from ia_funds.loader import _clean_fund_name, append_column_from_series

IA_YIELD_URL = "https://ia.ca/api/sites/ia/fund/yield"


def _unwrap(cell: Any) -> Any:
    if isinstance(cell, dict) and "value" in cell:
        return cell.get("value")
    return cell


def fetch_yield_snapshot(
    as_of: date | datetime | str,
    *,
    fund_type: Literal["savings", "insurance"] = "savings",
    locale: str = "en-ca",
    session: requests.Session | None = None,
    timeout: float = 60.0,
) -> pd.DataFrame:
    """
    Download the same snapshot used by https://ia.ca/funds-performance (Savings tab).

    This returns one row per product/fund series with net unit value and return columns.
    For many days at once, use ``fetch_yield_history`` (day-by-day requests compiled to wide CSV).
    """
    if isinstance(as_of, str):
        d = pd.to_datetime(as_of).date()
    elif isinstance(as_of, datetime):
        d = as_of.date()
    else:
        d = as_of

    params = {"locale": locale, "fundType": fund_type, "date": d.isoformat()}
    sess = session or requests.Session()
    r = sess.get(IA_YIELD_URL, params=params, headers={"User-Agent": "ia-funds-metastock/0.1"}, timeout=timeout)
    r.raise_for_status()
    rows: list[dict[str, Any]] = r.json()
    if not rows:
        return pd.DataFrame()

    flat: list[dict[str, Any]] = []
    for row in rows:
        flat.append(
            {
                "fundName": _clean_fund_name(row.get("fundName", "")),
                "fundTelusCode": row.get("fundTelusCode"),
                "fundCode": row.get("fundCode"),
                "netUnitValue": _unwrap(row.get("netUnitValue")),
                "netReturnYtd": _unwrap(row.get("netReturnYearToDate")),
                "lastYearReturn": _unwrap(row.get("lastYearReturn")),
                "netReturns1Month": _unwrap(row.get("netReturns1Month")),
                "netReturns3Months": _unwrap(row.get("netReturns3Months")),
                "netReturns6Months": _unwrap(row.get("netReturns6Months")),
                "netReturns1Year": _unwrap(row.get("netReturns1Year")),
                "netReturns3Years": _unwrap(row.get("netReturns3Years")),
                "netReturns5Years": _unwrap(row.get("netReturns5Years")),
                "netReturns10Years": _unwrap(row.get("netReturns10Years")),
            }
        )
    return pd.DataFrame.from_records(flat)


def dedupe_snapshot_by_code(snapshot: pd.DataFrame) -> pd.DataFrame:
    """
    Collapse multiple API rows per `fundTelusCode` (different internal product IDs) to one NAV per code.

    Rows are sorted by `fundCode` for stable ordering, then the first row per code is kept.
    """
    if snapshot.empty:
        return snapshot
    df = snapshot.copy()
    df = df.dropna(subset=["fundTelusCode", "netUnitValue"])
    if "fundCode" in df.columns:
        df = df.sort_values(["fundTelusCode", "fundCode"], na_position="last")
    return df.drop_duplicates(subset=["fundTelusCode"], keep="first").reset_index(drop=True)


def snapshots_to_long(frames: list[tuple[date, pd.DataFrame]]) -> pd.DataFrame:
    """Concatenate per-day snapshots into one long table: date, Funds, Code, netUnitValue, ..."""
    pieces: list[pd.DataFrame] = []
    for d, snap in frames:
        if snap is None or snap.empty:
            continue
        s = dedupe_snapshot_by_code(snap)
        if s.empty:
            continue
        chunk = s.assign(date=pd.Timestamp(d))
        pieces.append(chunk)
    if not pieces:
        return pd.DataFrame()
    return pd.concat(pieces, ignore_index=True)


def long_nav_to_wide(long_df: pd.DataFrame) -> pd.DataFrame:
    """
    Build the wide matrix expected by `load_wide_csv`: Funds, Asset class, Code, <ISO dates...>.

    Pivots on **Code** (Telus / display code) so minor ``fundName`` text changes across days do not
    duplicate rows. The fund title is the first non-null name in chronological order per code.
    """
    if long_df.empty:
        return pd.DataFrame(columns=["Funds", "Asset class", "Code"])

    df = long_df.copy()
    name_col = "Funds" if "Funds" in df.columns else "fundName"
    code_col = "Code" if "Code" in df.columns else "fundTelusCode"
    df = df.rename(columns={name_col: "Funds", code_col: "Code"})
    df["date"] = pd.to_datetime(df["date"]).dt.normalize()
    df = df.dropna(subset=["Code", "netUnitValue", "date"])

    df = df.sort_values("date")
    first_name = df.groupby("Code", sort=False)["Funds"].first()

    wide = df.pivot_table(index="Code", columns="date", values="netUnitValue", aggfunc="first")
    wide = wide.sort_index(axis=1)
    wide.columns = [c.strftime("%Y-%m-%d") for c in wide.columns]
    wide = wide.reset_index()
    wide.insert(0, "Funds", wide["Code"].map(first_name))
    wide.insert(1, "Asset class", "")
    cols = ["Funds", "Asset class", "Code"] + [c for c in wide.columns if c not in ("Funds", "Asset class", "Code")]
    return wide[cols]


def fetch_yield_history(
    start: date | datetime | str,
    end: date | datetime | str,
    *,
    fund_type: Literal["savings", "insurance"] = "savings",
    locale: str = "en-ca",
    session: requests.Session | None = None,
    timeout: float = 60.0,
    sleep_seconds: float = 0.25,
    weekdays_only: bool = False,
    fail_fast: bool = False,
    progress: Callable[[date, int, int, str], None] | None = None,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Reconstruct NAV history by calling `/api/sites/ia/fund/yield` once per calendar day in the range.

    Returns ``(wide, long)`` where **wide** matches manual CSV layout and **long** has one row per
    fund per day with columns including ``fundName``, ``fundTelusCode``, ``date``, ``netUnitValue``.

    Notes:
    - This issues one HTTP request per day; use a modest `--sleep` to reduce load on iA servers.
    - Weekends and holidays may return empty data; those days are skipped in the output columns.
    """
    d0 = pd.to_datetime(start).date()
    d1 = pd.to_datetime(end).date()
    if d1 < d0:
        raise ValueError("end date must be on or after start date")

    day = timedelta(days=1)
    dates: list[date] = []
    cur = d0
    while cur <= d1:
        if not weekdays_only or cur.weekday() < 5:
            dates.append(cur)
        cur = cur + day

    sess = session or requests.Session()
    collected: list[tuple[date, pd.DataFrame]] = []
    total = len(dates)

    for i, d in enumerate(dates, start=1):
        msg = ""
        try:
            snap = fetch_yield_snapshot(d, fund_type=fund_type, locale=locale, session=sess, timeout=timeout)
            collected.append((d, snap))
            msg = f"{len(snap)} rows" if not snap.empty else "empty"
        except requests.HTTPError as e:
            msg = f"HTTP {e.response.status_code if e.response is not None else '?'}"
            if fail_fast:
                raise
            collected.append((d, pd.DataFrame()))
        except requests.RequestException as e:
            msg = str(e)[:120]
            if fail_fast:
                raise
            collected.append((d, pd.DataFrame()))

        if progress is not None:
            progress(d, i, total, msg)
        elif msg != "empty":
            print(f"[{i}/{total}] {d.isoformat()} {msg}", file=sys.stderr, flush=True)

        if sleep_seconds > 0 and i < total:
            time.sleep(sleep_seconds)

    long_df = snapshots_to_long(collected)
    if long_df.empty:
        wide = pd.DataFrame(columns=["Funds", "Asset class", "Code"])
        return wide, long_df
    wide = long_nav_to_wide(long_df)
    return wide, long_df


def merge_nav_into_wide(wide: pd.DataFrame, snapshot: pd.DataFrame, as_of: date | datetime | str) -> pd.DataFrame:
    """Append netUnitValue from snapshot keyed by Code == fundTelusCode."""
    if snapshot.empty:
        return wide
    s = dedupe_snapshot_by_code(snapshot)
    series = s.set_index("fundTelusCode")["netUnitValue"]
    return append_column_from_series(wide, series, as_of)
