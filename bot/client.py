"""
Binance Futures Testnet REST API client wrapper.
Handles authentication, request signing, and HTTP communication.
"""

import hashlib
import hmac
import logging
import time
from urllib.parse import urlencode
from typing import Any, Optional

import requests

logger = logging.getLogger(__name__)

BASE_URL = "https://testnet.binancefuture.com"


class BinanceClientError(Exception):
    """Raised when the Binance API returns an error response."""
    def __init__(self, code: int, message: str):
        self.code = code
        self.message = message
        super().__init__(f"Binance API Error {code}: {message}")


class NetworkError(Exception):
    """Raised on network/connectivity failures."""


class BinanceFuturesClient:
    """
    Lightweight wrapper around the Binance Futures Testnet REST API.
    Handles HMAC-SHA256 signing for authenticated endpoints.
    """

    def __init__(self, api_key: str, api_secret: str, base_url: str = BASE_URL):
        self.api_key = api_key
        self.api_secret = api_secret
        self.base_url = base_url.rstrip("/")
        self.session = requests.Session()
        self.session.headers.update({
            "X-MBX-APIKEY": self.api_key,
            "Content-Type": "application/x-www-form-urlencoded",
        })

    # ------------------------------------------------------------------ #
    #  Internal helpers                                                    #
    # ------------------------------------------------------------------ #

    def _sign(self, params: dict) -> str:
        """Return HMAC-SHA256 signature for the given parameter dict."""
        query = urlencode(params)
        return hmac.new(
            self.api_secret.encode("utf-8"),
            query.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()

    def _request(
        self,
        method: str,
        path: str,
        params: Optional[dict] = None,
        signed: bool = False,
    ) -> Any:
        """
        Execute an HTTP request and return the parsed JSON response.

        Args:
            method:  HTTP verb (GET / POST / DELETE).
            path:    API path, e.g. '/fapi/v1/order'.
            params:  Query / body parameters.
            signed:  Whether to add timestamp + HMAC signature.

        Returns:
            Parsed JSON (dict or list).

        Raises:
            BinanceClientError: API-level error returned by Binance.
            NetworkError:       Connection / timeout failures.
        """
        params = params or {}

        if signed:
            params["timestamp"] = int(time.time() * 1000)
            params["signature"] = self._sign(params)

        url = f"{self.base_url}{path}"
        log_params = {k: v for k, v in params.items() if k != "signature"}

        logger.debug("→ %s %s  params=%s", method.upper(), path, log_params)

        try:
            if method.upper() == "GET":
                response = self.session.get(url, params=params, timeout=10)
            elif method.upper() == "POST":
                response = self.session.post(url, data=params, timeout=10)
            elif method.upper() == "DELETE":
                response = self.session.delete(url, params=params, timeout=10)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
        except requests.exceptions.ConnectionError as exc:
            logger.error("Network connection error: %s", exc)
            raise NetworkError(f"Could not connect to {self.base_url}: {exc}") from exc
        except requests.exceptions.Timeout as exc:
            logger.error("Request timed out: %s", exc)
            raise NetworkError(f"Request timed out: {exc}") from exc

        logger.debug("← %s %s", response.status_code, response.text[:500])

        data = response.json()

        # Binance error responses carry a numeric 'code' key (negative values)
        if isinstance(data, dict) and "code" in data and data["code"] != 200:
            logger.error("Binance API error: %s", data)
            raise BinanceClientError(data["code"], data.get("msg", "Unknown error"))

        return data

    # ------------------------------------------------------------------ #
    #  Public API methods                                                  #
    # ------------------------------------------------------------------ #

    def get_exchange_info(self) -> dict:
        """Fetch exchange trading rules and symbol metadata."""
        return self._request("GET", "/fapi/v1/exchangeInfo")

    def get_account(self) -> dict:
        """Fetch account information including balances."""
        return self._request("GET", "/fapi/v2/account", signed=True)

    def place_order(self, **kwargs) -> dict:
        """
        Place a new futures order.

        Required kwargs (at minimum):
            symbol   : e.g. 'BTCUSDT'
            side     : 'BUY' or 'SELL'
            type     : 'MARKET' or 'LIMIT'
            quantity : order quantity

        Additional for LIMIT:
            price        : limit price
            timeInForce  : 'GTC' (default applied by caller)

        Returns:
            Raw Binance order response dict.
        """
        logger.info(
            "Placing order → symbol=%s side=%s type=%s qty=%s price=%s",
            kwargs.get("symbol"),
            kwargs.get("side"),
            kwargs.get("type"),
            kwargs.get("quantity"),
            kwargs.get("price", "N/A"),
        )
        response = self._request("POST", "/fapi/v1/order", params=kwargs, signed=True)
        logger.info("Order placed → orderId=%s status=%s", response.get("orderId"), response.get("status"))
        return response

    def get_order(self, symbol: str, order_id: int) -> dict:
        """Query a specific order by symbol and orderId."""
        return self._request(
            "GET",
            "/fapi/v1/order",
            params={"symbol": symbol, "orderId": order_id},
            signed=True,
        )

    def cancel_order(self, symbol: str, order_id: int) -> dict:
        """Cancel an open order."""
        return self._request(
            "DELETE",
            "/fapi/v1/order",
            params={"symbol": symbol, "orderId": order_id},
            signed=True,
        )