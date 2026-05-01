from decimal import Decimal, InvalidOperation
from typing import Optional

VALID_SIDES = {"BUY", "SELL"}
VALID_ORDER_TYPES = {"MARKET", "LIMIT", "STOP_MARKET"}

def validate_symbol(symbol):
    s = symbol.strip().upper()
    if not s.isalpha() or len(s) < 3:
        raise ValueError(f"Invalid symbol '{symbol}'.")
    return s

def validate_side(side):
    s = side.strip().upper()
    if s not in VALID_SIDES:
        raise ValueError(f"Invalid side '{side}'. Must be BUY or SELL.")
    return s

def validate_order_type(order_type):
    t = order_type.strip().upper()
    if t not in VALID_ORDER_TYPES:
        raise ValueError(f"Invalid order type '{order_type}'.")
    return t

def validate_quantity(quantity):
    try:
        q = Decimal(str(quantity))
        if q <= 0:
            raise ValueError("Quantity must be greater than zero.")
        return str(q)
    except InvalidOperation:
        raise ValueError(f"Invalid quantity '{quantity}'.")

def validate_price(price):
    if price is None:
        return None
    try:
        p = Decimal(str(price))
        if p <= 0:
            raise ValueError("Price must be greater than zero.")
        return str(p)
    except InvalidOperation:
        raise ValueError(f"Invalid price '{price}'.")

def validate_order_params(symbol, side, order_type, quantity, price=None, stop_price=None):
    params = {
        "symbol": validate_symbol(symbol),
        "side": validate_side(side),
        "type": validate_order_type(order_type),
        "quantity": validate_quantity(quantity),
    }
    if params["type"] == "LIMIT":
        if price is None:
            raise ValueError("Price is required for LIMIT orders.")
        params["price"] = validate_price(price)
        params["timeInForce"] = "GTC"
    elif params["type"] == "STOP_MARKET":
        if stop_price is None:
            raise ValueError("Stop price is required for STOP_MARKET orders.")
        params["stopPrice"] = validate_price(stop_price)
    elif params["type"] == "MARKET":
        if price is not None:
            raise ValueError("Price should not be provided for MARKET orders.")
    return params