from __future__ import annotations

import html
import re
from datetime import datetime
from io import StringIO

import pandas as pd


def _clean_fund_name(name: str) -> str:
    if not isinstance(name, str):
        return str(name)
    t = html.unescape(name)
    t = re.sub(r"<[^>]+>", "", t)
    return t.replace("\xa0", " ").strip()


def load_wide_csv(path: str) -> tuple[pd.DataFrame, list[pd.Timestamp]]:
    """
    Load the wide export: Funds, Asset class, Code, <dates...>.

    Returns (wide_frame, sorted_date_columns as timestamps).
    """
    df = pd.read_csv(path, dtype=str, keep_default_na=False)
    if df.shape[1] < 4:
        raise ValueError("Expected at least columns: Funds, Asset class, Code, plus one or more date columns.")

    meta_cols = ["Funds", "Asset class", "Code"]
    for c in meta_cols:
        if c not in df.columns:
            raise ValueError(f"Missing required column: {c!r}")

    date_cols = [c for c in df.columns if c not in meta_cols]
    rename: dict[str, str] = {}
    for col in date_cols:
        if not str(col).strip():
            continue
        ts = pd.to_datetime(col, dayfirst=True, errors="coerce")
        if pd.isna(ts):
            continue
        norm = ts.normalize()
        rename[col] = norm.strftime("%Y-%m-%d")

    if not rename:
        raise ValueError("No parseable date columns found after the first three metadata columns.")

    df = df.rename(columns=rename)
    new_date_cols = sorted(set(rename.values()))
    for c in meta_cols:
        df[c] = df[c].astype(str).str.strip()
    df["Funds"] = df["Funds"].map(_clean_fund_name)

    wide = df[meta_cols + new_date_cols].copy()
    for c in new_date_cols:
        wide[c] = pd.to_numeric(wide[c].replace("", pd.NA), errors="coerce")

    dts = sorted(pd.to_datetime(new_date_cols, errors="coerce").tolist())
    return wide, dts


def wide_to_long(wide: pd.DataFrame) -> pd.DataFrame:
    """Melt wide NAV table to long format: date, code, name, asset_class, nav."""
    meta = ["Funds", "Asset class", "Code"]
    value_vars = [c for c in wide.columns if c not in meta]
    long = wide.melt(id_vars=meta, value_vars=value_vars, var_name="date", value_name="nav")
    long["date"] = pd.to_datetime(long["date"], errors="coerce")
    long = long.dropna(subset=["date", "nav"])
    long = long.sort_values(["Code", "date"])
    return long.reset_index(drop=True)


def append_column_from_series(wide: pd.DataFrame, series: pd.Series, column_date: datetime | pd.Timestamp) -> pd.DataFrame:
    """Append a single new date column aligned on Code (outer join on index Code)."""
    col = pd.to_datetime(column_date).strftime("%Y-%m-%d")
    s = series.copy()
    s.name = col
    keyed = wide.set_index("Code")
    if col in keyed.columns:
        keyed = keyed.drop(columns=[col])
    out = keyed.join(s, how="left").reset_index()
    # Reorder: meta + sorted date columns
    meta = ["Funds", "Asset class", "Code"]
    dates = sorted([c for c in out.columns if c not in meta])
    return out[meta + dates]
