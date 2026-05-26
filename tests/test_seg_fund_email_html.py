import pandas as pd

from ia_funds.report_email import build_summary_table, html_email_body


def test_html_email_matches_seg_fund_shell():
    wide = pd.DataFrame(
        {
            "Funds": ["Fund A", "Fund B"],
            "Asset class": ["Eq", "Eq"],
            "Code": ["FU1-P5", "FU2-P5"],
            "2025-04-28": ["10.0", "20.0"],
            "2025-04-29": ["10.5", "19.0"],
        }
    )
    html = html_email_body(wide)
    assert "<!DOCTYPE html>" in html
    assert "Fund analysis" in html
    assert "weekly" in html and "monthly" in html
    assert "Weekly indicators" in html
    assert "Monthly indicators" in html
    assert 'class="indicators-table"' in html
    assert "Indicators are mathematical summaries of past prices, not investment advice." in html
    assert "Data as of 2025-04-29" in html
    assert "FU1-P5" in html and "10.5000" in html


def test_build_summary_table_prior_nav():
    wide = pd.DataFrame(
        {
            "Funds": ["X"],
            "Asset class": [""],
            "Code": ["C1"],
            "2025-04-28": [10.0],
            "2025-04-29": [11.0],
        }
    )
    s = build_summary_table(wide)
    assert "prior_nav" in s.columns
    assert s.iloc[0]["last_nav"] == 11.0
    assert s.iloc[0]["prior_nav"] == 10.0
