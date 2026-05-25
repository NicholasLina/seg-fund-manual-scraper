from __future__ import annotations

import argparse
import sys
from pathlib import Path

from ia_funds.excel_export import export_workbook
from ia_funds.loader import load_wide_csv, wide_to_long
from ia_funds.metastock import export_per_ticker_files, wide_csv_to_metastock
from ia_funds.report_email import send_report_smtp
from ia_funds.scraper import fetch_yield_snapshot, merge_nav_into_wide


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
    snap = fetch_yield_snapshot(args.date, fund_type=args.fund_type, locale=args.locale)
    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
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

    pf = sub.add_parser("fetch", help="Fetch snapshot from ia.ca API")
    pf.add_argument("--date", required=True, help="As-of date (YYYY-MM-DD)")
    pf.add_argument("--fund-type", choices=("savings", "insurance"), default="savings")
    pf.add_argument("--locale", default="en-ca")
    pf.add_argument("--output", required=True, help="Snapshot CSV path")
    pf.add_argument("--merge-wide", dest="merge_wide", default=None, help="Existing wide NAV CSV to append column onto")
    pf.add_argument("--merge-out", dest="merge_out", default=None, help="Output for merged wide (default: overwrite --merge-wide)")
    pf.set_defaults(func=cmd_fetch)

    return p


def main(argv: list[str] | None = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)
    raise SystemExit(args.func(args))


if __name__ == "__main__":
    main()
