from ia_funds.loader import load_wide_csv, wide_to_long


def test_load_and_long_roundtrip():
    wide, dts = load_wide_csv("tests/fixtures/tiny_wide.csv")
    assert list(wide.columns[:3]) == ["Funds", "Asset class", "Code"]
    assert "2025-04-28" in wide.columns
    long = wide_to_long(wide)
    assert len(long) == 4
    assert set(long["Code"]) == {"FU155-P5", "FU070-P5"}
