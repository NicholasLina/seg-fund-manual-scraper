# ia-funds-metastock

Python toolkit inspired by manual segregated-fund workflows (similar in spirit to a small **seg-fund-scraper**): take iA **wide-format NAV CSVs** (Funds, Asset class, Code, then many date columns), and produce:

- **MetaStock DownLoader–friendly ASCII** (multi-symbol daily file, or one file per ticker)
- **Excel** workbook (wide matrix, long history, simple summary)
- **HTML email reports** (via SMTP)
- **Live data** from iA’s public API used by [Fund performance and overview](https://ia.ca/funds-performance) (`/api/sites/ia/fund/yield`): single-day snapshot, optional merge into a wide file, or **day-by-day history** over a date range compiled into wide/long CSVs.

## Install

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

## Input format

Your source file should look like the export you attached:

- Column A: `Funds`
- Column B: `Asset class`
- Column C: `Code` (for example `FU155-P5`, matching `fundTelusCode` from the site API)
- Remaining columns: dates as `DD/MM/YYYY` headers and NAV values

Malformed date headers are skipped; empty trailing columns are ignored.

## Commands

```bash
# Single ASCII file for MetaStock DownLoader (Tools → Convert, source = ASCII)
ia-funds metastock --input path/to/wide.csv --output out/metastock_daily.csv

# One CSV per ticker under a folder
ia-funds metastock --input path/to/wide.csv --output out/per_ticker --split

# Excel: sheets Wide, Long, Summary
ia-funds excel --input path/to/wide.csv --output out/report.xlsx

# Email (configure SMTP via environment – see below)
ia-funds email --input path/to/wide.csv --subject "Daily iA funds"
```

### Live fetch (single day or full history from the API)

The site loads data from `https://ia.ca/api/sites/ia/fund/yield` with query parameters `locale`, `fundType` (`savings` or `insurance`), and `date` (`YYYY-MM-DD`).

**Single snapshot** (one day, many funds — same as before):

```bash
ia-funds fetch --date 2026-05-22 --output out/snapshot.csv

# Only funds under **Series 75/100 Prestige 500** (matches `fundProductId` from the site catalog)
ia-funds fetch --date 2026-05-22 --output out/prestige500.csv \
  --fund-product-name "Series 75/100 Prestige 500"

# Same filter for a full day-by-day history rebuild
ia-funds fetch --from-date 2025-04-01 --to-date 2025-04-30 --output out/history_wide.csv \
  --fund-product-name "Series 75/100 Prestige 500"

# List product names and UUIDs (copy/paste for --fund-product-id)
ia-funds list-products
ia-funds list-products --output products.csv
```

Other filters:

- `--fund-product-id <uuid>` (repeatable) — use raw UUID(s) without scraping names.
- `--fund-product-contains <substring>` — must match **exactly one** product name (case-insensitive); if several match, the command errors and prints candidates.

You can combine `--fund-product-id` with `--fund-product-name` to merge multiple products into one download.

# Merge net unit value into an existing wide NAV file (matches on Code ↔ fundTelusCode)
ia-funds fetch --date 2026-05-22 --output out/snapshot.csv \
  --merge-wide path/to/master_wide.csv --merge-out path/to/master_wide_updated.csv
```

**Day-by-day history** rebuilds a wide matrix by calling the API once per calendar day between `--from-date` and `--to-date` (inclusive), deduplicating multiple rows per `fundTelusCode`, then pivoting NAVs into columns. This can take a long time and many requests; use `--sleep` (default 0.25s) to limit server load. Empty responses (weekends, holidays, or dates with no data) simply omit that column.

```bash
ia-funds fetch --from-date 2025-04-01 --to-date 2025-04-30 --output out/history_wide.csv

# Also write long format (one row per fund per day)
ia-funds fetch --from-date 2025-04-01 --to-date 2025-04-30 \
  --output out/history_wide.csv --long-output out/history_long.csv

# Only weekdays; abort on first HTTP error
ia-funds fetch --from-date 2025-01-01 --to-date 2025-06-01 --output out/wide.csv \
  --weekdays-only --fail-fast --sleep 0.3
```

Wide output columns use ISO dates (`YYYY-MM-DD`), compatible with `ia-funds metastock` / `load_wide_csv`.

## MetaStock notes

The exporter writes rows like:

`TICKER,D,YYYYMMDD,000000,OPEN,HIGH,LOW,CLOSE,0,0`

with `OPEN=HIGH=LOW=CLOSE=NAV` because the source is daily net unit value only. The first line is a header: `TICKER,PER,DATE,TIME,OPEN,HIGH,LOW,CLOSE,VOLUME,OPENINT`. In MetaStock 13+, use **Local Data Lists** or **The DownLoader → Convert** and set the source type to **ASCII text**, then convert to MetaStock format.

Ticker symbols are lightly sanitized (unsafe characters replaced); fund codes such as `FU155-P5` are kept when valid.

## Email environment variables

| Variable | Meaning |
|----------|---------|
| `SMTP_HOST` | SMTP server (default `localhost`) |
| `SMTP_PORT` | Port (default `587`) |
| `SMTP_USER` / `SMTP_PASSWORD` | Credentials if required |
| `SMTP_TLS` | `1` (default) to call `STARTTLS`, set `0` to disable |
| `MAIL_FROM` | From address |
| `MAIL_TO` | Recipient |

## Relationship to **seg-fund-scraper**

That repository is not vendored here. This project mirrors the same practical goals—**ingest fund data, transform it, distribute reports**—using iA’s wide NAV export and (optionally) their public JSON snapshot API.

## License

MIT
