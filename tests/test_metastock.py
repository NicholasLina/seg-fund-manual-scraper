from pathlib import Path

from ia_funds.loader import load_wide_csv, wide_to_long
from ia_funds.metastock import export_metastock_ascii, wide_csv_to_metastock


def test_metastock_header_and_sorted(tmp_path: Path):
    wide, _ = load_wide_csv("tests/fixtures/tiny_wide.csv")
    out = wide_csv_to_metastock(wide, tmp_path / "all.csv")
    text = out.read_text(encoding="utf-8").splitlines()
    assert text[0].startswith("TICKER,PER,DATE,TIME,OPEN")
    body = text[1:]
    assert any(line.startswith("FU155-P5,D,20250428") for line in body)
    assert any(line.startswith("FU070-P5,D,20250428") for line in body)


def test_per_ticker(tmp_path: Path):
    wide, _ = load_wide_csv("tests/fixtures/tiny_wide.csv")
    long = wide_to_long(wide)
    p1 = tmp_path / "one.csv"
    export_metastock_ascii(long[long["Code"] == "FU155-P5"], p1)
    lines = p1.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 3  # header + 2 days
