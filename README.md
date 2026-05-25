# ia-funds-metastock

Python toolkit inspired by manual segregated-fund workflows (similar in spirit to a small **seg-fund-scraper**): take iA **wide-format NAV CSVs** (Funds, Asset class, Code, then many date columns), and produce:

- **MetaStock DownLoader–friendly ASCII** (multi-symbol daily file, or one file per ticker)
- **Excel** workbook (wide matrix, long history, simple summary)
- **HTML email reports** (via SMTP)
- **Live snapshot fetch** from iA’s public API used by [Fund performance and overview](https://ia.ca/funds-performance) (`/api/sites/ia/fund/yield`)

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

### Live fetch (append latest NAV column)

The site loads data from `https://ia.ca/api/sites/ia/fund/yield` with query parameters `locale`, `fundType` (`savings` or `insurance`), and `date` (`YYYY-MM-DD`). This returns **one snapshot** (many rows for each fund series), not full history. Typical use: append today’s column to your master wide CSV.

```bash
ia-funds fetch --date 2026-05-22 --output out/snapshot.csv

# Merge net unit value into an existing wide NAV file (matches on Code ↔ fundTelusCode)
ia-funds fetch --date 2026-05-22 --output out/snapshot.csv \
  --merge-wide path/to/master_wide.csv --merge-out path/to/master_wide_updated.csv
```

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
