from __future__ import annotations

from datetime import date, datetime
from typing import Any, Literal

import pandas as pd
import requests

from ia_funds.loader import _clean_fund_name, append_column_from_series

IA_YIELD_URL = "https://ia.ca/api/sites/ia/fund/yield"


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
    It does not replace a full historical NAV matrix; use it to append the latest day
    to an existing wide CSV or to refresh a daily report.
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


def _unwrap(cell: Any) -> Any:
    if isinstance(cell, dict) and "value" in cell:
        return cell.get("value")
    return cell


def merge_nav_into_wide(wide: pd.DataFrame, snapshot: pd.DataFrame, as_of: date | datetime | str) -> pd.DataFrame:
    """Append netUnitValue from snapshot keyed by Code == fundTelusCode."""
    if snapshot.empty:
        return wide
    s = snapshot.dropna(subset=["fundTelusCode", "netUnitValue"]).drop_duplicates(subset=["fundTelusCode"])
    series = s.set_index("fundTelusCode")["netUnitValue"]
    return append_column_from_series(wide, series, as_of)
