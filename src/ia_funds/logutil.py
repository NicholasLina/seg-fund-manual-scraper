"""Configure stderr logging for the ``ia_funds`` package (CLI and library use)."""

from __future__ import annotations

import logging
import sys


def configure_logging(*, verbose: int = 0, quiet: bool = False) -> None:
    """
    Attach a stderr handler once and tune levels.

    - Default: INFO on ``ia_funds`` (progress-style messages).
    - ``-q`` / ``quiet``: WARNING on ``ia_funds`` (errors/warnings only).
    - ``-v``: INFO (explicit; same as default for this package).
    - ``-vv``: DEBUG on ``ia_funds``; root set to DEBUG so debug records reach the handler.
    """
    root = logging.getLogger()
    if not root.handlers:
        h = logging.StreamHandler(sys.stderr)
        h.setFormatter(logging.Formatter("%(levelname)s %(name)s: %(message)s"))
        root.addHandler(h)

    for name in ("urllib3", "urllib3.connectionpool", "requests"):
        logging.getLogger(name).setLevel(logging.WARNING)

    pkg = logging.getLogger("ia_funds")
    if verbose >= 2:
        root.setLevel(logging.DEBUG)
        pkg.setLevel(logging.DEBUG)
    else:
        root.setLevel(logging.INFO)
        if quiet:
            pkg.setLevel(logging.WARNING)
        else:
            pkg.setLevel(logging.INFO)
