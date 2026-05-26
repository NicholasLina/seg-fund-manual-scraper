from __future__ import annotations

import argparse
from pathlib import Path

from ia_funds.excel_export import export_workbook
from ia_funds.loader import load_wide_csv, wide_to_long
from ia_funds.metastock import export_per_ticker_files, wide_csv_to_metastock
from ia_funds.report_email import send_report_smtp
from ia_funds.scraper import fetch_yield_history, fetch_yield_snapshot, merge_nav_into_wide


def cmd_metastock(args: argparse.Namespace) -> int:
    wide, _ = load_wide_csv(args.input)
    out = Path(args.output)
    if args.split:
        paths = export_per_ticker_files(wide_to_long(wide), out)
        print(f"Wrote {len(paths)} files under {out}")
    else:
        p = wide_csv_to_metastock(wide, out)
        print(f"Wrote {p}")
    return 0


def cmd_excel(args: argparse.Namespace) -> int:
    wide, _ = load_wide_csv(args.input)
    p = export_workbook(wide, args.output)
    print(f"Wrote {p}")
    return 0


def cmd_email(args: argparse.Namespace) -> int:
    wide, _ = load_wide_csv(args.input)
    send_report_smtp(wide, args.subject, mail_from=args.mail_from, mail_to=args.mail_to)
    print("Sent.")
    return 0


def cmd_fetch(args: argparse.Namespace) -> int:
    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)

    if args.from_date and args.to_date:
        wide, long_df = fetch_yield_history(
            args.from_date,
            args.to_date,
            fund_type=args.fund_type,
            locale=args.locale,
            sleep_seconds=args.sleep,
            weekdays_only=args.weekdays_only,
            fail_fast=args.fail_fast,
        )
        wide.to_csv(out, index=False)
        date_cols = [c for c in wide.columns if c not in ("Funds", "Asset class", "Code")]
        print(f"Wrote {out} ({len(wide)} funds, {len(date_cols)} date columns)")
        if args.long_output:
            lp = Path(args.long_output)
            lp.parent.mkdir(parents=True, exist_ok=True)
            long_df.to_csv(lp, index=False)
            print(f"Wrote long format: {lp} ({len(long_df)} rows)")
        return 0

    if args.from_date or args.to_date:
        print("error: both --from-date and --to-date are required for history mode", flush=True)
        return 2

    snap = fetch_yield_snapshot(args.date, fund_type=args.fund_type, locale=args.locale)
    snap.to_csv(out, index=False)
    print(f"Wrote {out} ({len(snap)} rows)")
    if args.merge_wide:
        wide, _ = load_wide_csv(args.merge_wide)
        merged = merge_nav_into_wide(wide, snap, args.date)
        mpath = Path(args.merge_out or args.merge_wide)
        mpath.parent.mkdir(parents=True, exist_ok=True)
        merged.to_csv(mpath, index=False)
        print(f"Updated wide CSV: {mpath}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="ia-funds", description="iA funds → MetaStock / Excel / email / live fetch")
    sub = p.add_subparsers(dest="cmd", required=True)

    pm = sub.add_parser("metastock", help="Export MetaStock-compatible ASCII CSV")
    pm.add_argument("--input", required=True, help="Wide CSV path")
    pm.add_argument("--output", required=True, help="Output file, or directory with --split")
    pm.add_argument("--split", action="store_true", help="Write one ASCII file per ticker")
    pm.set_defaults(func=cmd_metastock)

    pe = sub.add_parser("excel", help="Write multi-sheet Excel workbook")
    pe.add_argument("--input", required=True)
    pe.add_argument("--output", required=True)
    pe.set_defaults(func=cmd_excel)

    pr = sub.add_parser("email", help="Send HTML summary via SMTP")
    pr.add_argument("--input", required=True)
    pr.add_argument("--subject", default="iA funds performance report")
    pr.add_argument("--mail-from", dest="mail_from", default=None)
    pr.add_argument("--mail-to", dest="mail_to", default=None)
    pr.set_defaults(func=cmd_email)

    pf = sub.add_parser("fetch", help="Fetch snapshot or day-by-day history from ia.ca API")
    pf.add_argument(
        "--date",
        default=None,
        help="Single as-of date (YYYY-MM-DD). Ignored when --from-date and --to-date are set.",
    )
    pf.add_argument(
        "--from-date",
        dest="from_date",
        default=None,
        help="Start date for history rebuild (requires --to-date). One API request per day.",
    )
    pf.add_argument(
        "--to-date",
        dest="to_date",
        default=None,
        help="End date for history rebuild (inclusive).",
    )
    pf.add_argument("--fund-type", choices=("savings", "insurance"), default="savings")
    pf.add_argument("--locale", default="en-ca")
    pf.add_argument("--output", required=True, help="Output CSV (snapshot or wide history)")
    pf.add_argument(
        "--long-output",
        dest="long_output",
        default=None,
        help="With history mode: also write melted long CSV to this path",
    )
    pf.add_argument(
        "--sleep",
        type=float,
        default=0.25,
        help="Seconds to sleep between history requests (default: 0.25)",
    )
    pf.add_argument(
        "--weekdays-only",
        action="store_true",
        help="Only request Mon–Fri (still one call per weekday)",
    )
    pf.add_argument("--fail-fast", action="store_true", help="Abort on first HTTP/network error")
    pf.add_argument("--merge-wide", dest="merge_wide", default=None, help="(single-day mode) wide CSV to merge into")
    pf.add_argument("--merge-out", dest="merge_out", default=None, help="(single-day mode) merged wide output path")
    pf.set_defaults(func=cmd_fetch)

    return p


def main(argv: list[str] | None = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.cmd == "fetch" and not args.from_date and not args.to_date and not args.date:
        parser.error("fetch requires either --date (single day) or both --from-date and --to-date (history)")
    raise SystemExit(args.func(args))


if __name__ == "__main__":
    main()
