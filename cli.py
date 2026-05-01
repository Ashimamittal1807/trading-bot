#!/usr/bin/env python3
"""
cli.py – Command-line interface entry point for the Binance Futures trading bot.

Usage examples
--------------
# Market BUY
python cli.py --symbol BTCUSDT --side BUY --type MARKET --quantity 0.001

# Limit SELL
python cli.py --symbol BTCUSDT --side SELL --type LIMIT --quantity 0.001 --price 95000

# Stop-Market BUY (bonus order type)
python cli.py --symbol BTCUSDT --side BUY --type STOP_MARKET --quantity 0.001 --stop-price 85000

# Override credentials without .env (not recommended for production)
python cli.py --api-key KEY --api-secret SECRET --symbol ETHUSDT --side BUY --type MARKET --quantity 0.01
"""

import argparse
import os
import sys
from pathlib import Path

# ── Load .env if python-dotenv is available ───────────────────────────────── #
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # dotenv is optional

from bot.client import BinanceFuturesClient
from bot.logging_config import setup_logging
from bot.orders import place_order


TESTNET_BASE_URL = "https://testnet.binancefuture.com"

BANNER = r"""
  ____  _                            _____           _ _               ____        _
 | __ )(_)_ __   __ _ _ __   ___ ___|_   _| __ __ _  __| (_)_ __   __ _  | __ )  ___ | |_
 |  _ \| | '_ \ / _` | '_ \ / __/ _ \ | || '__/ _` |/ _` | | '_ \ / _` | |  _ \ / _ \| __|
 | |_) | | | | | (_| | | | | (_|  __/ | || | | (_| | (_| | | | | | (_| | | |_) | (_) | |_
 |____/|_|_| |_|\__,_|_| |_|\___\___| |_||_|  \__,_|\__,_|_|_| |_|\__, | |____/ \___/ \__|
                                                                     |___/
              Binance Futures Testnet  ·  USDT-M Perpetuals
"""


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="trading_bot",
        description="Place orders on Binance Futures Testnet (USDT-M).",
        formatter_class=argparse.RawTextHelpFormatter,
        epilog=__doc__,
    )

    # ── Credentials (fall back to env vars) ──────────────────────────────── #
    creds = parser.add_argument_group("API credentials (or set env vars)")
    creds.add_argument(
        "--api-key",
        default=os.getenv("BINANCE_API_KEY", ""),
        metavar="KEY",
        help="Binance Futures Testnet API key  [env: BINANCE_API_KEY]",
    )
    creds.add_argument(
        "--api-secret",
        default=os.getenv("BINANCE_API_SECRET", ""),
        metavar="SECRET",
        help="Binance Futures Testnet API secret  [env: BINANCE_API_SECRET]",
    )

    # ── Order parameters ──────────────────────────────────────────────────── #
    order = parser.add_argument_group("Order parameters")
    order.add_argument(
        "--symbol", required=True,
        help="Trading pair, e.g. BTCUSDT",
    )
    order.add_argument(
        "--side", required=True, choices=["BUY", "SELL"],
        help="Order side: BUY or SELL",
    )
    order.add_argument(
        "--type", required=True,
        dest="order_type",
        choices=["MARKET", "LIMIT", "STOP_MARKET"],
        help="Order type: MARKET | LIMIT | STOP_MARKET",
    )
    order.add_argument(
        "--quantity", required=True,
        help="Order quantity (in base asset units, e.g. 0.001 for BTC)",
    )
    order.add_argument(
        "--price",
        default=None,
        help="Limit price — required for LIMIT orders",
    )
    order.add_argument(
        "--stop-price",
        dest="stop_price",
        default=None,
        help="Stop trigger price — required for STOP_MARKET orders",
    )

    # ── Misc ─────────────────────────────────────────────────────────────── #
    misc = parser.add_argument_group("Misc")
    misc.add_argument(
        "--log-dir",
        default="logs",
        help="Directory for log files (default: logs/)",
    )
    misc.add_argument(
        "--base-url",
        default=TESTNET_BASE_URL,
        help=f"Binance base URL (default: {TESTNET_BASE_URL})",
    )
    misc.add_argument(
        "--no-banner",
        action="store_true",
        help="Suppress the ASCII banner",
    )

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    # ── Logging ───────────────────────────────────────────────────────────── #
    setup_logging(log_dir=args.log_dir)

    if not args.no_banner:
        print(BANNER)

    # ── Credential check ──────────────────────────────────────────────────── #
    missing = []
    if not args.api_key:
        missing.append("--api-key (or BINANCE_API_KEY env var)")
    if not args.api_secret:
        missing.append("--api-secret (or BINANCE_API_SECRET env var)")
    if missing:
        print("❌  Missing required credentials:")
        for m in missing:
            print(f"     • {m}")
        print(
            "\nTip: create a .env file in the project root:\n"
            "     BINANCE_API_KEY=your_key\n"
            "     BINANCE_API_SECRET=your_secret\n"
        )
        return 1

    # ── Build client ──────────────────────────────────────────────────────── #
    client = BinanceFuturesClient(
        api_key=args.api_key,
        api_secret=args.api_secret,
        base_url=args.base_url,
    )

    # ── Place order ───────────────────────────────────────────────────────── #
    return place_order(
        client=client,
        symbol=args.symbol,
        side=args.side,
        order_type=args.order_type,
        quantity=args.quantity,
        price=args.price,
        stop_price=args.stop_price,
    )


if __name__ == "__main__":
    sys.exit(main())