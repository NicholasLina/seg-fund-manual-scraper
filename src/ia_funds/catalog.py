"""Parse iA savings fund *product* list embedded in the public funds-performance HTML."""

from __future__ import annotations

import codecs
import html as html_lib
import logging
import re

import pandas as pd
import requests

log = logging.getLogger(__name__)


def _funds_performance_url(locale: str) -> str:
    loc = (locale or "en-ca").lower()
    if loc.startswith("fr"):
        return "https://ia.ca/rendement-fonds"
    return "https://ia.ca/funds-performance"


def _decode_embedded_name(raw: str) -> str:
    """Decode JSON-style escapes used inside the Next.js string (e.g. \\u003c)."""
    try:
        s = codecs.decode(raw, "unicode_escape")
    except Exception:
        s = raw
    return html_lib.unescape(s.replace("\\/", "/")).strip()


def fetch_fund_product_catalog(
    locale: str = "en-ca",
    *,
    session: requests.Session | None = None,
    timeout: float = 60.0,
) -> pd.DataFrame:
    """
    Return product rows embedded in the savings fund performance page: ``product_id``, ``name``.

    These ``product_id`` values match ``fundProductId`` in ``/api/sites/ia/fund/yield`` responses.
    """
    url = _funds_performance_url(locale)
    sess = session or requests.Session()
    log.info("Downloading fund product catalog: %s", url)
    r = sess.get(url, headers={"User-Agent": "ia-funds-metastock/0.1"}, timeout=timeout)
    r.raise_for_status()
    df = parse_product_catalog_html(r.text)
    log.info("Product catalog: %d products", len(df))
    return df


def parse_product_catalog_html(page_html: str) -> pd.DataFrame:
    pat = re.compile(
        r'\\"id\\":\\"([0-9a-f-]{36})\\",\\"isAvailable\\":(?:true|false),\\"name\\":\\"((?:[^\\]|\\.)*?)\\"'
    )
    rows: list[dict[str, str]] = []
    for product_id, raw_name in pat.findall(page_html):
        name = _decode_embedded_name(raw_name)
        rows.append({"product_id": product_id, "name": name, "name_raw": raw_name})
    if not rows:
        log.debug("parse_product_catalog_html: no product id/name matches in HTML")
        return pd.DataFrame(columns=["product_id", "name", "name_raw"])
    df = pd.DataFrame(rows).drop_duplicates(subset=["product_id"])
    out = df.sort_values("name").reset_index(drop=True)
    log.debug("parse_product_catalog_html: %d unique products from regex", len(out))
    return out


def resolve_fund_product_ids(
    catalog: pd.DataFrame,
    *,
    exact_names: list[str] | None = None,
    contains: str | None = None,
    explicit_ids: list[str] | None = None,
) -> list[str]:
    """
    Resolve CLI selections to a list of ``fundProductId`` UUID strings.

    ``exact_names`` are compared after stripping; match is case-sensitive on the decoded catalog name.
    ``contains`` must match exactly one catalog row (substring, case-insensitive).
    """
    ids: list[str] = []
    if explicit_ids:
        ids.extend(explicit_ids)
    if exact_names:
        for wanted in exact_names:
            w = wanted.strip()
            hits = catalog[catalog["name"].str.strip().str.casefold() == w.casefold()]
            if hits.empty:
                raise ValueError(f"No fund product named exactly {wanted!r}. Run `ia-funds list-products` to see names.")
            ids.extend(hits["product_id"].tolist())
    if contains:
        needle = contains.strip().lower()
        if not needle:
            raise ValueError("contains filter must be non-empty")
        mask = catalog["name"].str.lower().str.contains(re.escape(needle), regex=True)
        hits = catalog[mask]
        if len(hits) == 0:
            raise ValueError(f"No product name contains {contains!r}. Run `ia-funds list-products`.")
        if len(hits) > 1:
            preview = "\n".join(f"  {r['name']}  ({r['product_id']})" for _, r in hits.head(20).iterrows())
            raise ValueError(
                f"Product name substring {contains!r} matches {len(hits)} products; "
                f"use --fund-product-name with an exact name or --fund-product-id.\n{preview}"
            )
        ids.append(hits.iloc[0]["product_id"])
    # de-dupe preserving order
    seen: set[str] = set()
    out: list[str] = []
    for i in ids:
        if i not in seen:
            seen.add(i)
            out.append(i)
    log.debug("resolve_fund_product_ids: resolved to %d unique id(s)", len(out))
    return out
