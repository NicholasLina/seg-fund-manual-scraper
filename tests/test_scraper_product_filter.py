from unittest.mock import MagicMock, patch

import pandas as pd

from ia_funds.scraper import fetch_yield_snapshot


def test_fetch_yield_snapshot_filters_by_fund_product_id():
    payload = [
        {
            "fundProductId": "aaa",
            "fundTelusCode": "X",
            "fundName": "A",
            "fundCode": "c1",
            "netUnitValue": {"value": 1.0},
        },
        {
            "fundProductId": "bbb",
            "fundTelusCode": "Y",
            "fundName": "B",
            "fundCode": "c2",
            "netUnitValue": {"value": 2.0},
        },
    ]
    mock_resp = MagicMock()
    mock_resp.json.return_value = payload
    mock_resp.raise_for_status = MagicMock()

    with patch("ia_funds.scraper.requests.Session.get", return_value=mock_resp):
        sess = __import__("requests").Session()
        df = fetch_yield_snapshot("2026-01-01", session=sess, fund_product_ids=["BBB"])
    assert len(df) == 1
    assert df.iloc[0]["fundTelusCode"] == "Y"
