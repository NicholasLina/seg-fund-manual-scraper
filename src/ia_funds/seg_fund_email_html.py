"""Build the same HTML shell as seg-fund-scraper ``fund_email_analysis.write_polished_html`` (NAV data).

Layout, CSS, tabs, sortable tables, footer, and chart modal fragment are aligned with
https://github.com/NicholasLina/seg-fund-scraper — wide NAV rows populate the weekly and
monthly indicator panels (identical table); the Filter tab shows an empty state like an
empty top-picks run in the upstream tool.
"""

from __future__ import annotations

import html
from pathlib import Path

import pandas as pd

from ia_funds.seg_fund_chart_embed import build_chart_viewer_html


def _read_asset(name: str) -> str:
    return (Path(__file__).resolve().parent / name).read_text(encoding="utf-8")


def _fmt_num(val: object, *, decimals: int = 4) -> str:
    if val is None or (isinstance(val, float) and pd.isna(val)):
        return "\u2014"
    try:
        x = float(val)
    except (TypeError, ValueError):
        return "\u2014"
    if pd.isna(x):
        return "\u2014"
    return f"{x:.{decimals}f}"


def _fmt_pct(val: object) -> str:
    if val is None or (isinstance(val, float) and pd.isna(val)):
        return "\u2014"
    try:
        x = float(val)
    except (TypeError, ValueError):
        return "\u2014"
    if pd.isna(x):
        return "\u2014"
    return f"{x * 100:.2f}%"


def _render_nav_indicators_table(summary: pd.DataFrame, esc) -> str:
    """Table using the same classes as seg-fund ``_render_table_html`` (Fund + Chart + numeric columns)."""
    if summary.empty:
        return '<p class="empty">No rows available.</p>'

    has_last = "last_nav" in summary.columns and "as_of" in summary.columns
    hdr_last = str(summary["as_of"].iloc[0]) if has_last else "NAV"

    head_parts: list[str] = [
        f'<th scope="col" class="sortable">{esc("Fund")}</th>',
        f'<th scope="col" class="no-sort">{esc("Chart")}</th>',
        f'<th scope="col" class="sortable">{esc("Code")}</th>',
        f'<th scope="col" class="sortable">{esc("Asset class")}</th>',
    ]
    if has_last:
        head_parts.append(f'<th scope="col" class="sortable">{esc(hdr_last)}</th>')
    if "prior_nav" in summary.columns:
        head_parts.append(f'<th scope="col" class="sortable">{esc("Prior NAV")}</th>')
    if "pct_vs_prior" in summary.columns:
        head_parts.append(f'<th scope="col" class="sortable">{esc("% vs prior")}</th>')
    head = "<tr>" + "".join(head_parts) + "</tr>"

    body_lines: list[str] = []
    for _, row in summary.iterrows():
        tds: list[str] = []
        # Fund
        fn = row.get("Funds", "")
        cell = "" if pd.isna(fn) else str(fn)
        title = f' title="{esc(cell)}"'
        tds.append(f"<td{title}>{esc(cell)}</td>")
        # Chart (no OHLC in wide NAV export)
        tds.append('<td class="chart-cell">\u2014</td>')
        # Code
        c = row.get("Code", "")
        c = "" if pd.isna(c) else str(c)
        tds.append(f"<td>{esc(c)}</td>")
        # Asset class
        ac = row.get("Asset class", "")
        ac = "" if pd.isna(ac) else str(ac)
        tds.append(f"<td>{esc(ac)}</td>")
        if has_last:
            tds.append(f'<td class="num">{esc(_fmt_num(row.get("last_nav")))}</td>')
        if "prior_nav" in summary.columns:
            tds.append(f'<td class="num">{esc(_fmt_num(row.get("prior_nav")))}</td>')
        if "pct_vs_prior" in summary.columns:
            tds.append(f'<td class="num">{esc(_fmt_pct(row.get("pct_vs_prior")))}</td>')
        body_lines.append("<tr>" + "".join(tds) + "</tr>")

    return (
        '<table role="grid" class="indicators-table">\n'
        f"<thead>{head}</thead>\n<tbody>\n{''.join(body_lines)}\n</tbody>\n</table>"
    )


def build_fund_analysis_email_html(
    summary: pd.DataFrame,
    *,
    data_as_of: str,
) -> str:
    """Full HTML document matching seg-fund-scraper fund analysis email layout."""
    esc = html.escape
    page_style = _read_asset("_seg_fund_page_style.htmlfrag")
    table_sort_script = "<script>\n" + _read_asset("_seg_fund_table_sort.js.txt") + "\n</script>\n"
    chart_block = build_chart_viewer_html("{}")

    nav_table = _render_nav_indicators_table(summary, esc)

    top_picks_panel = f"""      <div class="tab-panel panel-top" role="tabpanel">
        <div class="table-wrap">
          <p class="empty">No rows available.</p>
        </div>
      </div>"""

    doc = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>{esc("Fund analysis — weekly & monthly")}</title>
{page_style}
</head>
<body>
  <div class="page">
    <header class="mast">
      <h1>Fund analysis</h1>
      <p class="meta">Data as of {esc(data_as_of)}</p>
    </header>

    <!-- Interactive charts: open in a modern browser; requires JS + network for the chart library CDN. -->
    <section class="card tab-card" aria-label="Indicator tables">
      <input class="tab-input" type="radio" name="tf-view" id="view-top" checked>
      <input class="tab-input" type="radio" name="tf-view" id="view-weekly">
      <input class="tab-input" type="radio" name="tf-view" id="view-monthly">
      <div class="tab-bar" role="tablist">
        <label class="tab" for="view-top" role="tab">Filter</label>
        <label class="tab" for="view-weekly" role="tab">Weekly indicators</label>
        <label class="tab" for="view-monthly" role="tab">Monthly indicators</label>
      </div>
{top_picks_panel}
      <div class="tab-panel panel-w" role="tabpanel">
        <div class="table-wrap">
          {nav_table}
        </div>
      </div>
      <div class="tab-panel panel-m" role="tabpanel">
        <div class="table-wrap">
          {nav_table}
        </div>
      </div>
    </section>

    <footer>Indicators are mathematical summaries of past prices, not investment advice.</footer>
  </div>

"""
    doc += "\n" + table_sort_script + "\n" + chart_block + "\n</body>\n</html>\n"
    return doc
