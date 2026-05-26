"""iA funds performance → MetaStock / Excel / email tooling."""

from ia_funds.report_email import (
    build_summary_table,
    generate_fund_analysis_html,
    send_report_smtp,
    write_fund_analysis_html,
)

__version__ = "0.1.0"

__all__ = [
    "__version__",
    "build_summary_table",
    "generate_fund_analysis_html",
    "write_fund_analysis_html",
    "send_report_smtp",
]
