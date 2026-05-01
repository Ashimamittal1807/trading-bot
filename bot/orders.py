"""
Order placement logic layer.
Sits between the CLI and the raw BinanceFuturesClient,
providing formatted output and structured results.
"""

import logging
from typing import Optional

from bot.client import BinanceFuturesClient, BinanceClientError, NetworkError
from bot.validators import validate_order_params

logger = logging.getLogger(__name__)


def _fmt_order_summary(params: dict) -> str:
    """Return a human-readable summary of the order parameters."""
    lines = [
        "┌─── Order Request Summary ───────────────────────────",
        f"│  Symbol     : {params['symbol']}",
        f"│  Side       : {params['side']}",
        f"│  Type       : {params['type']}",
        f"│  Quantity   : {params['quantity']}",
    ]
    if "price" in params:
        lines.append(f"│  Price      : {params['price']}")
    if "stopPrice" in params:
        lines.append(f"│  Stop Price : {params['stopPrice']}")
    if "timeInForce" in params:
        lines.append(f"│  TIF        : {params['timeInForce']}")
    lines.append("└─────────────────────────────────────────────────────")
    return "\n".join(lines)


def _fmt_order_response(response: dict) -> str:
    """Return a human-readable summary of the Binance order response."""
    lines = [
        "┌─── Order Response ──────────────────────────────────",
        f"│  Order ID   : {response.get('orderId', 'N/A')}",
        f"│  Symbol     : {response.get('symbol', 'N/A')}",
        f"│  Status     : {response.get('status', 'N/A')}",
        f"│  Side       : {response.get('side', 'N/A')}",
        f"│  Type       : {response.get('type', 'N/A')}",
        f"│  Quantity   : {response.get('origQty', 'N/A')}",
        f"│  Executed   : {response.get('executedQty', 'N/A')}",
        f"│  Avg Price  : {response.get('avgPrice', response.get('price', 'N/A'))}",
        f"│  Client OID : {response.get('clientOrderId', 'N/A')}",
        f"│  Time       : {response.get('updateTime', 'N/A')}",
        "└─────────────────────────────────────────────────────",
    ]
    return "\n".join(lines)


def place_order(
    client: BinanceFuturesClient,
    symbol: str,
    side: str,
    order_type: str,
    quantity: str,
    price: Optional[str] = None,
    stop_price: Optional[str] = None,
) -> int:
    """
    Validate inputs, place an order, and print formatted results.

    Returns:
        0 on success, 1 on failure.
    """
    # ── Validate ──────────────────────────────────────────────────────── #
    try:
        params = validate_order_params(
            symbol=symbol,
            side=side,
            order_type=order_type,
            quantity=quantity,
            price=price,
            stop_price=stop_price,
        )
    except ValueError as exc:
        logger.error("Validation error: %s", exc)
        print(f"\n❌  Validation Error: {exc}\n")
        return 1

    # ── Print request summary ─────────────────────────────────────────── #
    print()
    print(_fmt_order_summary(params))

    # ── Place order ───────────────────────────────────────────────────── #
    try:
        response = client.place_order(**params)
    except BinanceClientError as exc:
        logger.error("API error placing order: code=%s msg=%s", exc.code, exc.message)
        print(f"\n❌  Binance API Error [{exc.code}]: {exc.message}\n")
        return 1
    except NetworkError as exc:
        logger.error("Network error placing order: %s", exc)
        print(f"\n❌  Network Error: {exc}\n")
        return 1
    except Exception as exc:  # noqa: BLE001
        logger.exception("Unexpected error placing order")
        print(f"\n❌  Unexpected Error: {exc}\n")
        return 1

    # ── Print response ────────────────────────────────────────────────── #
    print()
    print(_fmt_order_response(response))
    print("\n✅  Order placed successfully!\n")
    return 0