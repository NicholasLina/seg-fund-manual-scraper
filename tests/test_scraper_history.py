from datetime import date
from unittest.mock import patch

import pandas as pd

from ia_funds.scraper import dedupe_snapshot_by_code, fetch_yield_history, long_nav_to_wide, snapshots_to_long


def test_dedupe_snapshot_by_code():
    df = pd.DataFrame(
        {
            "fundTelusCode": ["FU-A", "FU-A", "FU-B"],
            "fundCode": ["X2", "X1", "Y1"],
            "netUnitValue": [10.0, 10.5, 9.0],
        }
    )
    out = dedupe_snapshot_by_code(df)
    assert len(out) == 2
    assert out.set_index("fundTelusCode").loc["FU-A", "netUnitValue"] == 10.5


def test_snapshots_to_long_and_wide_stable_name():
    d1 = date(2025, 4, 28)
    d2 = date(2025, 4, 29)
    s1 = pd.DataFrame(
        {
            "fundName": ["Fund X"],
            "fundTelusCode": ["FU1-P5"],
            "fundCode": ["C1"],
            "netUnitValue": [10.0],
        }
    )
    s2 = pd.DataFrame(
        {
            "fundName": ["Fund X variant"],
            "fundTelusCode": ["FU1-P5"],
            "fundCode": ["C1"],
            "netUnitValue": [10.1],
        }
    )
    long_df = snapshots_to_long([(d1, s1), (d2, s2)])
    wide = long_nav_to_wide(long_df)
    assert len(wide) == 1
    assert "2025-04-28" in wide.columns and "2025-04-29" in wide.columns
    assert wide.iloc[0]["Funds"] == "Fund X"


def test_fetch_yield_history_compiles():
    def fake_fetch(d, **kwargs):
        if d == date(2025, 1, 1):
            return pd.DataFrame(
                {
                    "fundName": ["A"],
                    "fundTelusCode": ["FU1-P5"],
                    "fundCode": ["C1"],
                    "netUnitValue": [1.0],
                }
            )
        if d == date(2025, 1, 2):
            return pd.DataFrame(
                {
                    "fundName": ["A"],
                    "fundTelusCode": ["FU1-P5"],
                    "fundCode": ["C1"],
                    "netUnitValue": [1.1],
                }
            )
        return pd.DataFrame()

    with patch("ia_funds.scraper.fetch_yield_snapshot", side_effect=fake_fetch):
        wide, long_df = fetch_yield_history(
            "2025-01-01",
            "2025-01-02",
            sleep_seconds=0,
        )
    assert len(wide) == 1
    assert len(long_df) == 2
    assert wide.iloc[0]["2025-01-01"] == 1.0
    assert wide.iloc[0]["2025-01-02"] == 1.1
