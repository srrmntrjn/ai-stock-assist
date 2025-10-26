"""Free market data fetcher built on top of public CoinGecko endpoints."""

from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import datetime, timedelta
from threading import Lock
from typing import Any, Dict, Iterable, List, Optional, Tuple

import requests
from requests import Response
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from src.logger import log


@dataclass
class _CacheEntry:
    """Simple container for cached values with an expiry timestamp."""

    value: Any
    expires_at: datetime


class MarketDataFetcher:
    """Fetch free market data from public APIs with lightweight caching."""

    def __init__(
        self,
        session: Optional[requests.Session] = None,
        price_ttl: int = 30,
        ohlcv_ttl: int = 60,
    ) -> None:
        self.coingecko_base = "https://api.coingecko.com/api/v3"
        self.session = session or requests.Session()
        self.price_cache_ttl = timedelta(seconds=max(price_ttl, 1))
        self.ohlcv_cache_ttl = timedelta(seconds=max(ohlcv_ttl, 1))

        self._price_cache: Dict[str, _CacheEntry] = {}
        self._ohlcv_cache: Dict[Tuple[str, int, int], _CacheEntry] = {}
        self._cache_lock = Lock()

        self._configure_session(self.session)

        # Symbol mappings
        self.symbol_to_coingecko = {
            "BTC-PERPETUAL": "bitcoin",
            "ETH-PERPETUAL": "ethereum",
            "SOL-PERPETUAL": "solana",
            "BNB-PERPETUAL": "binancecoin",
            "XRP-PERPETUAL": "ripple",
            "DOGE-PERPETUAL": "dogecoin",
        }

    def _configure_session(self, session: requests.Session) -> None:
        """Configure retry/backoff strategy and default headers."""

        retry = Retry(
            total=3,
            status_forcelist=(429, 500, 502, 503, 504),
            backoff_factor=0.5,
            allowed_methods=("GET",),
        )
        adapter = HTTPAdapter(max_retries=retry)
        session.mount("https://", adapter)
        session.mount("http://", adapter)
        session.headers.setdefault(
            "User-Agent",
            "ai-stock-assist/market-data-fetcher",
        )

    def _now(self) -> datetime:
        return datetime.utcnow()

    def _get_cached(self, cache: Dict[Any, _CacheEntry], key: Any) -> Optional[Any]:
        """Return cached value if present and not expired."""

        with self._cache_lock:
            entry = cache.get(key)
            if not entry:
                return None
            if entry.expires_at <= self._now():
                cache.pop(key, None)
                return None
            return entry.value

    def _set_cache(
        self,
        cache: Dict[Any, _CacheEntry],
        key: Any,
        value: Any,
        ttl: timedelta,
    ) -> None:
        with self._cache_lock:
            cache[key] = _CacheEntry(value=value, expires_at=self._now() + ttl)

    def _get_coingecko_id(self, symbol: str) -> str:
        """Convert internal symbol format (e.g. BTC-PERPETUAL) to CoinGecko ID."""

        normalized = symbol.upper()
        return self.symbol_to_coingecko.get(
            normalized,
            normalized.lower().replace("-perpetual", ""),
        )

    def _simple_price_request(self, coin_ids: Iterable[str]) -> Dict[str, Any]:
        url = f"{self.coingecko_base}/simple/price"
        params = {
            "ids": ",".join(coin_ids),
            "vs_currencies": "usd",
        }

        response = self.session.get(url, params=params, timeout=10)
        response.raise_for_status()
        return response.json()

    def get_current_price(self, symbol: str) -> float:
        """Get the latest USD price for a single symbol."""

        cache_key = symbol.upper()
        cached = self._get_cached(self._price_cache, cache_key)
        if cached is not None:
            return float(cached)

        try:
            coin_id = self._get_coingecko_id(symbol)
            data = self._simple_price_request([coin_id])
            price = float(data[coin_id]["usd"])
            self._set_cache(self._price_cache, cache_key, price, self.price_cache_ttl)
            log.debug(f"Fetched price for {symbol}: ${price:.4f}")
            return price

        except Exception as exc:
            log.error(f"Error fetching price for {symbol}: {exc}")
            raise

    def get_multiple_prices(self, symbols: List[str]) -> Dict[str, float]:
        """Fetch prices for multiple symbols, reusing cached values when possible."""

        results: Dict[str, float] = {}
        uncached: List[str] = []

        for symbol in symbols:
            cache_key = symbol.upper()
            cached = self._get_cached(self._price_cache, cache_key)
            if cached is not None:
                results[symbol] = float(cached)
            else:
                uncached.append(symbol)

        if not uncached:
            return results

        try:
            id_map = {symbol: self._get_coingecko_id(symbol) for symbol in uncached}
            data = self._simple_price_request(id_map.values())

            for symbol, coin_id in id_map.items():
                price = float(data.get(coin_id, {}).get("usd", 0.0))
                if price:
                    results[symbol] = price
                    self._set_cache(
                        self._price_cache,
                        symbol.upper(),
                        price,
                        self.price_cache_ttl,
                    )

            return results

        except Exception as exc:
            log.error(f"Error fetching multiple prices: {exc}")
            return results

    def _fetch_market_chart(self, coin_id: str, days: int, interval: str) -> Dict[str, Any]:
        url = f"{self.coingecko_base}/coins/{coin_id}/market_chart"
        params = {
            "vs_currency": "usd",
            "days": days,
            "interval": interval,
        }

        response: Response = self.session.get(url, params=params, timeout=10)
        response.raise_for_status()
        return response.json()

    def _determine_days(self, timeframe_minutes: int, limit: int) -> int:
        total_minutes = max(1, timeframe_minutes) * max(1, limit)
        if timeframe_minutes <= 60:
            estimated_days = math.ceil(total_minutes / (60 * 24))
            return max(1, min(7, estimated_days))

        total_hours = total_minutes / 60
        estimated_days = math.ceil(total_hours / 24)
        return max(1, min(90, estimated_days))

    def _aggregate_ohlcv(
        self,
        prices: List[List[float]],
        volumes: List[List[float]],
        timeframe_minutes: int,
    ) -> List[Dict[str, float]]:
        if not prices:
            return []

        timeframe_ms = max(1, timeframe_minutes) * 60 * 1000
        volume_map = {int(ts): float(vol) for ts, vol in volumes}

        aggregated: List[Dict[str, float]] = []
        bucket_prices: List[Tuple[int, float]] = []
        bucket_volumes: List[float] = []
        bucket_start: Optional[int] = None

        for ts, price in sorted(prices, key=lambda item: item[0]):
            timestamp = int(ts)
            bucket_id = (timestamp // timeframe_ms) * timeframe_ms

            if bucket_start is None:
                bucket_start = bucket_id

            if bucket_id != bucket_start and bucket_prices:
                aggregated.append(self._compose_candle(bucket_start, bucket_prices, bucket_volumes))
                bucket_prices = []
                bucket_volumes = []
                bucket_start = bucket_id

            bucket_prices.append((timestamp, float(price)))
            bucket_volumes.append(volume_map.get(timestamp, 0.0))

        if bucket_prices and bucket_start is not None:
            aggregated.append(self._compose_candle(bucket_start, bucket_prices, bucket_volumes))

        return aggregated

    @staticmethod
    def _compose_candle(
        bucket_start: int,
        price_points: List[Tuple[int, float]],
        volume_points: List[float],
    ) -> Dict[str, float]:
        open_price = price_points[0][1]
        close_price = price_points[-1][1]
        high_price = max(p[1] for p in price_points)
        low_price = min(p[1] for p in price_points)
        volume_total = float(sum(volume_points)) if volume_points else 0.0

        return {
            "timestamp": float(bucket_start),
            "open": float(open_price),
            "high": float(high_price),
            "low": float(low_price),
            "close": float(close_price),
            "volume": volume_total,
        }

    def get_ohlcv(
        self,
        symbol: str,
        timeframe_minutes: int = 3,
        limit: int = 100,
    ) -> List[Dict[str, float]]:
        """Get OHLCV data for a symbol aggregated to the requested timeframe."""

        cache_key = (symbol.upper(), timeframe_minutes, limit)
        cached = self._get_cached(self._ohlcv_cache, cache_key)
        if cached is not None:
            return list(cached)

        try:
            coin_id = self._get_coingecko_id(symbol)
            interval = "minutely" if timeframe_minutes <= 60 else "hourly"
            days = self._determine_days(timeframe_minutes, limit)
            raw = self._fetch_market_chart(coin_id, days, interval)

            ohlcv = self._aggregate_ohlcv(
                raw.get("prices", []),
                raw.get("total_volumes", []),
                timeframe_minutes,
            )

            result = ohlcv[-limit:]
            self._set_cache(self._ohlcv_cache, cache_key, result, self.ohlcv_cache_ttl)
            log.debug(f"Fetched {len(result)} candles for {symbol} ({timeframe_minutes}m)")
            return result

        except Exception as exc:
            log.error(f"Error fetching OHLCV for {symbol}: {exc}")
            raise

    def _fetch_coin_detail(self, coin_id: str) -> Dict[str, Any]:
        url = f"{self.coingecko_base}/coins/{coin_id}"
        response = self.session.get(url, timeout=10)
        response.raise_for_status()
        return response.json()

    def estimate_open_interest(self, symbol: str) -> float:
        """Estimate open interest using 24h volume as a proxy."""

        try:
            coin_id = self._get_coingecko_id(symbol)
            data = self._fetch_coin_detail(coin_id)

            volume_24h = (
                data.get("market_data", {})
                .get("total_volume", {})
                .get("usd", 0.0)
            )

            estimated_oi = float(volume_24h) * 0.2
            return estimated_oi

        except Exception as exc:
            log.warning(f"Could not estimate open interest for {symbol}: {exc}")
            return 0.0

    def estimate_funding_rate(self, symbol: str) -> float:
        """Return a neutral funding rate placeholder for free data sources."""

        _ = symbol  # Symbol kept for signature parity / logging if needed later
        return 0.00001

    def clear_cache(self) -> None:
        """Expose a helper to clear internal caches (useful for testing)."""

        with self._cache_lock:
            self._price_cache.clear()
            self._ohlcv_cache.clear()
