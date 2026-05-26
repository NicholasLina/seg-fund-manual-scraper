from __future__ import annotations

import logging
import time
from datetime import date, datetime, timedelta
from typing import Any, Callable, Literal, Sequence

import pandas as pd
import requests

from ia_funds.loader import _clean_fund_name, append_column_from_series

IA_YIELD_URL = "https://ia.ca/api/sites/ia/fund/yield"

log = logging.getLogger(__name__)


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
    fund_product_ids: Sequence[str] | None = None,
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
    log.debug("GET %s params=%s", IA_YIELD_URL, params)
    r = sess.get(IA_YIELD_URL, params=params, headers={"User-Agent": "ia-funds-metastock/0.1"}, timeout=timeout)
    r.raise_for_status()
    rows: list[dict[str, Any]] = r.json()
    if not rows:
        log.debug("Yield snapshot %s: API returned no rows", d.isoformat())
        return pd.DataFrame()

    if fund_product_ids:
        allow = {str(x).strip().lower() for x in fund_product_ids}
        n_before = len(rows)
        rows = [row for row in rows if str(row.get("fundProductId", "")).strip().lower() in allow]
        log.debug(
            "Yield snapshot %s: filtered %d -> %d rows by fund_product_ids",
            d.isoformat(),
            n_before,
            len(rows),
        )
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
    out = pd.DataFrame.from_records(flat)
    log.debug("Yield snapshot %s: %d rows after flatten", d.isoformat(), len(out))
    return out


def dedupe_snapshot_by_code(snapshot: pd.DataFrame) -> pd.DataFrame:
    """
    Collapse multiple API rows per `fundTelusCode` (different internal product IDs) to one NAV per code.

    Rows are sorted by `fundCode` for stable ordering, then the first row per code is kept.
    """
    if snapshot.empty:
        log.debug("dedupe_snapshot_by_code: empty input")
        return snapshot
    df = snapshot.copy()
    df = df.dropna(subset=["fundTelusCode", "netUnitValue"])
    if "fundCode" in df.columns:
        df = df.sort_values(["fundTelusCode", "fundCode"], na_position="last")
    out = df.drop_duplicates(subset=["fundTelusCode"], keep="first").reset_index(drop=True)
    log.debug("dedupe_snapshot_by_code: %d -> %d rows", len(snapshot), len(out))
    return out


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
        log.debug("snapshots_to_long: no non-empty days")
        return pd.DataFrame()
    long_df = pd.concat(pieces, ignore_index=True)
    log.debug("snapshots_to_long: %d rows from %d day frames", len(long_df), len(frames))
    return long_df


def long_nav_to_wide(long_df: pd.DataFrame) -> pd.DataFrame:
    """
    Build the wide matrix expected by `load_wide_csv`: Funds, Asset class, Code, <ISO dates...>.

    Pivots on **Code** (Telus / display code) so minor ``fundName`` text changes across days do not
    duplicate rows. The fund title is the first non-null name in chronological order per code.
    """
    if long_df.empty:
        log.debug("long_nav_to_wide: empty long frame")
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
    wide_out = wide[cols]
    log.debug(
        "long_nav_to_wide: %d codes, %d date columns",
        len(wide_out),
        len([c for c in wide_out.columns if c not in ("Funds", "Asset class", "Code")]),
    )
    return wide_out


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
    fund_product_ids: Sequence[str] | None = None,
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
    filt = f", product filter ({len(fund_product_ids)} ids)" if fund_product_ids else ""
    log.info(
        "fetch_yield_history: %s .. %s (%d days to request%s, sleep=%ss, weekdays_only=%s)",
        d0.isoformat(),
        d1.isoformat(),
        total,
        filt,
        sleep_seconds,
        weekdays_only,
    )

    for i, d in enumerate(dates, start=1):
        msg = ""
        request_failed = False
        try:
            snap = fetch_yield_snapshot(
                d,
                fund_type=fund_type,
                locale=locale,
                session=sess,
                timeout=timeout,
                fund_product_ids=fund_product_ids,
            )
            collected.append((d, snap))
            msg = f"{len(snap)} rows" if not snap.empty else "empty"
        except requests.HTTPError as e:
            msg = f"HTTP {e.response.status_code if e.response is not None else '?'}"
            log.warning("[%d/%d] %s %s", i, total, d.isoformat(), msg)
            request_failed = True
            if fail_fast:
                raise
            collected.append((d, pd.DataFrame()))
        except requests.RequestException as e:
            msg = str(e)[:120]
            log.warning("[%d/%d] %s %s", i, total, d.isoformat(), msg)
            request_failed = True
            if fail_fast:
                raise
            collected.append((d, pd.DataFrame()))

        if progress is not None:
            progress(d, i, total, msg)
        if not request_failed:
            if msg == "empty":
                log.debug("[%d/%d] %s empty", i, total, d.isoformat())
            else:
                log.info("[%d/%d] %s %s", i, total, d.isoformat(), msg)

        if sleep_seconds > 0 and i < total:
            time.sleep(sleep_seconds)

    long_df = snapshots_to_long(collected)
    if long_df.empty:
        log.info("fetch_yield_history: no NAV rows after combining days; returning empty wide/long")
        wide = pd.DataFrame(columns=["Funds", "Asset class", "Code"])
        return wide, long_df
    wide = long_nav_to_wide(long_df)
    date_cols = [c for c in wide.columns if c not in ("Funds", "Asset class", "Code")]
    log.info(
        "fetch_yield_history: done — wide %d funds × %d dates; long %d rows",
        len(wide),
        len(date_cols),
        len(long_df),
    )
    return wide, long_df


def merge_nav_into_wide(wide: pd.DataFrame, snapshot: pd.DataFrame, as_of: date | datetime | str) -> pd.DataFrame:
    """Append netUnitValue from snapshot keyed by Code == fundTelusCode."""
    if snapshot.empty:
        log.debug("merge_nav_into_wide: empty snapshot, wide unchanged (%d rows)", len(wide))
        return wide
    s = dedupe_snapshot_by_code(snapshot)
    series = s.set_index("fundTelusCode")["netUnitValue"]
    out = append_column_from_series(wide, series, as_of)
    col = pd.to_datetime(as_of).strftime("%Y-%m-%d")
    log.info("merge_nav_into_wide: appended column %s from %d snapshot codes", col, len(series))
    return out
