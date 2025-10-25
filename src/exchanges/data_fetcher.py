"""Free market data fetcher using CoinGecko and CryptoCompare APIs"""

import requests
from typing import List, Dict, Optional
from datetime import datetime, timedelta
from src.logger import log


class MarketDataFetcher:
    """Fetch free market data from public APIs"""

    def __init__(self):
        self.coingecko_base = "https://api.coingecko.com/api/v3"
        self.session = requests.Session()

        # Symbol mappings
        self.symbol_to_coingecko = {
            'BTC-PERPETUAL': 'bitcoin',
            'ETH-PERPETUAL': 'ethereum',
            'SOL-PERPETUAL': 'solana',
            'BNB-PERPETUAL': 'binancecoin',
            'XRP-PERPETUAL': 'ripple',
            'DOGE-PERPETUAL': 'dogecoin',
        }

    def _get_coingecko_id(self, symbol: str) -> str:
        """Convert symbol to CoinGecko ID"""
        return self.symbol_to_coingecko.get(symbol, symbol.lower().replace('-perpetual', ''))

    def get_current_price(self, symbol: str) -> float:
        """Get current price from CoinGecko"""
        try:
            coin_id = self._get_coingecko_id(symbol)
            url = f"{self.coingecko_base}/simple/price"
            params = {
                'ids': coin_id,
                'vs_currencies': 'usd'
            }

            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()

            price = data[coin_id]['usd']
            log.debug(f"Fetched price for {symbol}: ${price}")
            return float(price)

        except Exception as e:
            log.error(f"Error fetching price for {symbol}: {e}")
            raise

    def get_ohlcv(self, symbol: str, timeframe_minutes: int = 3, limit: int = 100) -> List[Dict]:
        """
        Get OHLCV data from CoinGecko

        Note: CoinGecko free API has limited granularity
        - 1-2 days: minute data (closest to 3min we can get)
        - 3-90 days: hourly data (for 4h timeframe)
        """
        try:
            coin_id = self._get_coingecko_id(symbol)

            # For 3-minute data, use 1-minute chart and aggregate
            if timeframe_minutes <= 60:
                days = 1  # Last 1 day for minute data
                url = f"{self.coingecko_base}/coins/{coin_id}/market_chart"
                params = {
                    'vs_currency': 'usd',
                    'days': days,
                    'interval': 'minutely'  # Actually ~5min intervals on free tier
                }
            else:
                # For 4-hour data
                days = 90  # Last 90 days for hourly data
                url = f"{self.coingecko_base}/coins/{coin_id}/market_chart"
                params = {
                    'vs_currency': 'usd',
                    'days': days,
                    'interval': 'hourly'
                }

            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()

            # CoinGecko returns: prices[[timestamp, price], ...], volumes[[timestamp, vol], ...]
            prices = data.get('prices', [])
            volumes = data.get('total_volumes', [])

            # Convert to OHLCV format (using price as OHLC for simplicity)
            ohlcv = []
            for i in range(min(len(prices), limit)):
                timestamp = prices[i][0]
                price = prices[i][1]
                volume = volumes[i][1] if i < len(volumes) else 0

                ohlcv.append({
                    'timestamp': timestamp,
                    'open': price,
                    'high': price * 1.001,  # Approximate
                    'low': price * 0.999,   # Approximate
                    'close': price,
                    'volume': volume
                })

            log.debug(f"Fetched {len(ohlcv)} candles for {symbol}")
            return ohlcv[-limit:]  # Return last N candles

        except Exception as e:
            log.error(f"Error fetching OHLCV for {symbol}: {e}")
            raise

    def get_multiple_prices(self, symbols: List[str]) -> Dict[str, float]:
        """Get prices for multiple symbols in one call"""
        try:
            coin_ids = [self._get_coingecko_id(s) for s in symbols]
            url = f"{self.coingecko_base}/simple/price"
            params = {
                'ids': ','.join(coin_ids),
                'vs_currencies': 'usd'
            }

            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()

            # Map back to original symbols
            prices = {}
            for symbol in symbols:
                coin_id = self._get_coingecko_id(symbol)
                if coin_id in data:
                    prices[symbol] = float(data[coin_id]['usd'])

            return prices

        except Exception as e:
            log.error(f"Error fetching multiple prices: {e}")
            return {}

    def estimate_open_interest(self, symbol: str) -> float:
        """
        Estimate open interest based on 24h volume
        (Real exchanges provide this, but for free APIs we estimate)
        """
        try:
            coin_id = self._get_coingecko_id(symbol)
            url = f"{self.coingecko_base}/coins/{coin_id}"

            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()

            # Estimate as percentage of market cap
            market_cap = data.get('market_data', {}).get('market_cap', {}).get('usd', 0)
            volume_24h = data.get('market_data', {}).get('total_volume', {}).get('usd', 0)

            # Rough estimate: OI is typically 10-30% of 24h volume for major cryptos
            estimated_oi = volume_24h * 0.2

            return float(estimated_oi)

        except Exception as e:
            log.warning(f"Could not estimate OI for {symbol}: {e}")
            return 0.0

    def estimate_funding_rate(self, symbol: str) -> float:
        """
        Estimate funding rate (typically between -0.01% to 0.01% every 8h)
        For free APIs, we return a neutral rate
        In production, use exchange's actual funding rate
        """
        # Neutral funding rate
        return 0.00001  # 0.001% per 8h (typical)
