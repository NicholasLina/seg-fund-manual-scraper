import pandas as pd

from ia_funds.catalog import parse_product_catalog_html, resolve_fund_product_ids


def test_parse_product_catalog_html_embedded_json():
    # Matches escaped JSON embedded in Next.js bundles (backslash-quote around keys).
    html = (
        r'foo\"id\":\"11111111-1111-1111-1111-111111111111\",\"isAvailable\":true,\"name\":\"Series 75/100 Prestige 500\"'
        r'bar\"id\":\"22222222-2222-2222-2222-222222222222\",\"isAvailable\":false,\"name\":\"Other Product\"'
    )
    cat = parse_product_catalog_html(html)
    assert len(cat) == 2
    row = cat.set_index("product_id").loc["11111111-1111-1111-1111-111111111111"]
    assert row["name"] == "Series 75/100 Prestige 500"


def test_resolve_exact_and_contains():
    cat = pd.DataFrame(
        {
            "product_id": ["p1", "p2"],
            "name": ["Series 75/100 Prestige 500", "Series 75/100 Prestige 500 F-Class"],
            "name_raw": ["", ""],
        }
    )
    assert resolve_fund_product_ids(cat, exact_names=["Series 75/100 Prestige 500"]) == ["p1"]
    assert resolve_fund_product_ids(cat, explicit_ids=["p2"]) == ["p2"]
    assert resolve_fund_product_ids(
        cat,
        exact_names=["series 75/100 prestige 500"],
    ) == ["p1"]
