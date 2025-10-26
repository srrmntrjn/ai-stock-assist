import importlib.util
import sys
import types
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

# Stub third-party modules that are not available in the test runtime
requests_module = types.ModuleType("requests")
requests_module.Session = MagicMock

adapters_module = types.ModuleType("requests.adapters")
adapters_module.HTTPAdapter = MagicMock
requests_module.adapters = adapters_module
requests_module.Response = MagicMock
sys.modules["requests"] = requests_module
sys.modules["requests.adapters"] = adapters_module

urllib3_module = types.ModuleType("urllib3")
util_module = types.ModuleType("urllib3.util")
retry_module = types.ModuleType("urllib3.util.retry")
retry_module.Retry = MagicMock
sys.modules["urllib3"] = urllib3_module
sys.modules["urllib3.util"] = util_module
sys.modules["urllib3.util.retry"] = retry_module

# Stub out src.logger to avoid pulling in heavy dependencies during tests
fake_logger_module = types.ModuleType("src.logger")
fake_logger = MagicMock()
fake_logger_module.log = fake_logger
sys.modules["src.logger"] = fake_logger_module

FETCHER_PATH = Path(__file__).resolve().parents[1] / "src" / "exchanges" / "data_fetcher.py"
spec = importlib.util.spec_from_file_location("src.exchanges.data_fetcher", FETCHER_PATH)
market_data_fetcher = importlib.util.module_from_spec(spec)
sys.modules["src.exchanges.data_fetcher"] = market_data_fetcher
spec.loader.exec_module(market_data_fetcher)
MarketDataFetcher = market_data_fetcher.MarketDataFetcher


class MarketDataFetcherTests(unittest.TestCase):
    def setUp(self) -> None:
        session = MagicMock()
        session.headers = {}
        self.fetcher = MarketDataFetcher(session=session, price_ttl=300, ohlcv_ttl=300)
        self.session = session

    def _mock_response(self, payload):
        response = MagicMock()
        response.json.return_value = payload
        response.raise_for_status.return_value = None
        return response

    def test_get_current_price_uses_cache(self):
        self.session.get.return_value = self._mock_response({"bitcoin": {"usd": 123.45}})

        price = self.fetcher.get_current_price("BTC-PERPETUAL")
        self.assertEqual(price, 123.45)
        self.session.get.assert_called_once()

        # Second call should be served from cache
        self.session.get.reset_mock()
        cached_price = self.fetcher.get_current_price("BTC-PERPETUAL")
        self.assertEqual(cached_price, 123.45)
        self.session.get.assert_not_called()

    def test_get_ohlcv_aggregates_prices(self):
        chart_data = {
            "prices": [
                [0, 100.0],
                [60_000, 110.0],
                [120_000, 105.0],
                [180_000, 120.0],
            ],
            "total_volumes": [
                [0, 10.0],
                [60_000, 20.0],
                [120_000, 30.0],
                [180_000, 40.0],
            ],
        }

        with patch.object(self.fetcher, "_fetch_market_chart", return_value=chart_data) as mock_chart:
            candles_first = self.fetcher.get_ohlcv("BTC-PERPETUAL", timeframe_minutes=2, limit=2)
            candles_second = self.fetcher.get_ohlcv("BTC-PERPETUAL", timeframe_minutes=2, limit=2)

        mock_chart.assert_called_once()

        self.assertEqual(len(candles_first), 2)
        self.assertEqual(candles_first[0]["open"], 100.0)
        self.assertEqual(candles_first[0]["close"], 110.0)
        self.assertEqual(candles_first[0]["high"], 110.0)
        self.assertEqual(candles_first[0]["low"], 100.0)
        self.assertEqual(candles_first[0]["volume"], 30.0)

        self.assertEqual(candles_first[1]["open"], 105.0)
        self.assertEqual(candles_first[1]["close"], 120.0)
        self.assertEqual(candles_first[1]["high"], 120.0)
        self.assertEqual(candles_first[1]["low"], 105.0)
        self.assertEqual(candles_first[1]["volume"], 70.0)

        # Cached result should equal the freshly computed one
        self.assertEqual(candles_first, candles_second)

    def test_estimate_open_interest(self):
        with patch.object(
            self.fetcher,
            "_fetch_coin_detail",
            return_value={"market_data": {"total_volume": {"usd": 5000.0}}},
        ):
            estimate = self.fetcher.estimate_open_interest("BTC-PERPETUAL")
            self.assertEqual(estimate, 1000.0)

        with patch.object(self.fetcher, "_fetch_coin_detail", side_effect=Exception("boom")):
            estimate = self.fetcher.estimate_open_interest("BTC-PERPETUAL")
            self.assertEqual(estimate, 0.0)


if __name__ == "__main__":
    unittest.main()
