"""
Logging configuration for the trading bot.
Sets up both a rotating file handler and a console handler.
"""

import logging
import logging.handlers
import os
from pathlib import Path


def setup_logging(log_dir: str = "logs", log_level: str = "DEBUG") -> None:
    """
    Configure root logger with:
      - Rotating file handler  → logs/trading_bot.log  (DEBUG+)
      - Console (stderr) handler → WARNING+ (quiet by default)

    Args:
        log_dir:   Directory where log files are written.
        log_level: Minimum level for the file handler.
    """
    log_path = Path(log_dir)
    log_path.mkdir(parents=True, exist_ok=True)

    numeric_level = getattr(logging, log_level.upper(), logging.DEBUG)

    root = logging.getLogger()
    root.setLevel(logging.DEBUG)

    # ── File handler (rotating, max 5 MB × 3 files) ───────────────────── #
    file_handler = logging.handlers.RotatingFileHandler(
        filename=log_path / "trading_bot.log",
        maxBytes=5 * 1024 * 1024,
        backupCount=3,
        encoding="utf-8",
    )
    file_handler.setLevel(numeric_level)
    file_fmt = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    file_handler.setFormatter(file_fmt)

    # ── Console handler (WARNING+ so CLI output stays clean) ─────────── #
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.WARNING)
    console_fmt = logging.Formatter("%(levelname)s: %(message)s")
    console_handler.setFormatter(console_fmt)

    root.addHandler(file_handler)
    root.addHandler(console_handler)

    logging.getLogger(__name__).debug(
        "Logging initialised → file=%s level=%s", log_path / "trading_bot.log", log_level
    )