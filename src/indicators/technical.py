"""Technical indicator calculations using pandas-ta."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Mapping, MutableMapping, Optional, Sequence, Union

import pandas as pd
import pandas_ta as ta

from src.exchanges.base import OHLCV
from src.exchanges.data_fetcher import MarketDataFetcher
from src.logger import log

CandleInput = Union[OHLCV, Mapping[str, Union[int, float, datetime]]]


@dataclass(frozen=True)
class IndicatorConfig:
    """Configuration values for indicator calculations."""

    ema_fast: int = 12
    ema_slow: int = 26
    macd_signal: int = 9
    rsi_length: int = 14
    atr_length: int = 14
    default_limit: int = 200
    timeframes: Optional[Mapping[str, int]] = None  # timeframe label -> minutes

    def __post_init__(self) -> None:
        if self.timeframes is None:
            object.__setattr__(self, "timeframes", {"3m": 3, "4h": 240})
        else:
            object.__setattr__(self, "timeframes", dict(self.timeframes))


@dataclass
class IndicatorSnapshot:
    """Container for the latest indicator values of a timeframe."""

    timeframe: str
    as_of: datetime
    close: float
    ema_fast: float
    ema_slow: float
    ema_trend: str
    macd: float
    macd_signal: float
    macd_hist: float
    rsi: float
    atr: float

    def to_dict(self) -> Dict[str, Union[str, float]]:
        """Return a serialisable representation of the snapshot."""

        return {
            "timeframe": self.timeframe,
            "as_of": self.as_of.isoformat(),
            "close": self.close,
            "ema_fast": self.ema_fast,
            "ema_slow": self.ema_slow,
            "ema_trend": self.ema_trend,
            "macd": self.macd,
            "macd_signal": self.macd_signal,
            "macd_hist": self.macd_hist,
            "rsi": self.rsi,
            "atr": self.atr,
        }


class TechnicalIndicatorCalculator:
    """Calculate technical indicators for one or more timeframes."""

    def __init__(
        self,
        data_fetcher: Optional[MarketDataFetcher] = None,
        config: Optional[IndicatorConfig] = None,
    ) -> None:
        self.data_fetcher = data_fetcher or MarketDataFetcher()
        self.config = config or IndicatorConfig()

    def calculate_for_symbol(
        self,
        symbol: str,
        *,
        limits: Optional[Mapping[str, int]] = None,
    ) -> Dict[str, IndicatorSnapshot]:
        """
        Fetch OHLCV data for the configured timeframes and calculate indicators.

        Args:
            symbol: Trading pair symbol, e.g. ``"BTC-PERPETUAL"``.
            limits: Optional override for the amount of candles per timeframe.

        Returns:
            Dictionary keyed by timeframe containing indicator snapshots.
        """

        results: Dict[str, IndicatorSnapshot] = {}
        for timeframe, minutes in self.config.timeframes.items():
            limit = (limits or {}).get(timeframe, self.config.default_limit)
            log.debug(
                "Calculating indicators",
                symbol=symbol,
                timeframe=timeframe,
                candles=limit,
            )
            ohlcv = self.data_fetcher.get_ohlcv(
                symbol,
                timeframe_minutes=minutes,
                limit=limit,
            )
            snapshot = self.calculate_from_candles(ohlcv, timeframe=timeframe)
            results[timeframe] = snapshot

        return results

    def calculate_from_candles(
        self,
        candles: Sequence[CandleInput],
        *,
        timeframe: str,
    ) -> IndicatorSnapshot:
        """Calculate indicators for a specific timeframe from raw candles."""

        if not candles:
            raise ValueError("At least one candle is required to calculate indicators")

        df = self._candles_to_dataframe(candles)
        indicator_df = self._build_indicator_frame(df)
        if indicator_df.empty:
            raise ValueError("Indicator calculation resulted in an empty dataset")

        latest = indicator_df.iloc[-1]
        timestamp = latest.name
        if hasattr(timestamp, "to_pydatetime"):
            timestamp = timestamp.to_pydatetime()
        if getattr(timestamp, "tzinfo", None) is not None:
            timestamp = timestamp.replace(tzinfo=None)

        ema_trend = "bullish" if latest["ema_fast"] > latest["ema_slow"] else "bearish"
        if abs(latest["ema_fast"] - latest["ema_slow"]) <= 1e-9:
            ema_trend = "neutral"

        snapshot = IndicatorSnapshot(
            timeframe=timeframe,
            as_of=timestamp,
            close=float(latest["close"]),
            ema_fast=float(latest["ema_fast"]),
            ema_slow=float(latest["ema_slow"]),
            ema_trend=ema_trend,
            macd=float(latest["macd"]),
            macd_signal=float(latest["macd_signal"]),
            macd_hist=float(latest["macd_hist"]),
            rsi=float(latest["rsi"]),
            atr=float(latest["atr"]),
        )

        log.debug(
            "Indicator snapshot",
            timeframe=timeframe,
            close=snapshot.close,
            ema_fast=snapshot.ema_fast,
            ema_slow=snapshot.ema_slow,
            macd=snapshot.macd,
            rsi=snapshot.rsi,
        )

        return snapshot

    @staticmethod
    def _candles_to_dataframe(candles: Sequence[CandleInput]) -> pd.DataFrame:
        """Convert various candle representations to a clean DataFrame."""

        records: List[MutableMapping[str, float]] = []
        for candle in candles:
            if isinstance(candle, OHLCV):
                timestamp = candle.timestamp
                record = {
                    "timestamp": timestamp,
                    "open": candle.open,
                    "high": candle.high,
                    "low": candle.low,
                    "close": candle.close,
                    "volume": candle.volume,
                }
            else:
                timestamp = candle.get("timestamp")
                record = {
                    "timestamp": timestamp,
                    "open": float(candle.get("open", 0.0)),
                    "high": float(candle.get("high", 0.0)),
                    "low": float(candle.get("low", 0.0)),
                    "close": float(candle.get("close", 0.0)),
                    "volume": float(candle.get("volume", 0.0)),
                }
            records.append(record)

        df = pd.DataFrame.from_records(records)
        if "timestamp" not in df.columns:
            raise ValueError("Candles must include a timestamp field")

        timestamps = df["timestamp"]
        if pd.api.types.is_numeric_dtype(timestamps):
            first_value = float(timestamps.iloc[0])
            unit = "ms" if abs(first_value) >= 1e12 else "s"
            parsed = pd.to_datetime(timestamps, unit=unit, utc=True)
        else:
            parsed = pd.to_datetime(timestamps, utc=True, errors="coerce")

        if parsed.isna().any():
            raise ValueError("Unable to parse candle timestamps")

        parsed_index = pd.DatetimeIndex(parsed)
        if parsed_index.tz is not None:
            parsed_index = parsed_index.tz_localize(None)

        df.index = parsed_index
        df = df.drop(columns=["timestamp"])
        df = df.sort_index()
        df = df.astype({"open": float, "high": float, "low": float, "close": float, "volume": float})
        return df

    def _build_indicator_frame(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add indicator columns to the OHLCV frame and drop incomplete rows."""

        close_series = df["close"]
        ema_fast = ta.ema(close_series, length=self.config.ema_fast)
        ema_slow = ta.ema(close_series, length=self.config.ema_slow)
        macd_df = ta.macd(
            close_series,
            fast=self.config.ema_fast,
            slow=self.config.ema_slow,
            signal=self.config.macd_signal,
        )
        if macd_df is None or macd_df.empty:
            raise ValueError("Unable to compute MACD values with the provided candles")

        macd_columns = list(macd_df.columns)
        if len(macd_columns) < 3:
            raise ValueError("Unexpected MACD output format")
        rsi = ta.rsi(close_series, length=self.config.rsi_length)
        atr = ta.atr(
            high=df["high"],
            low=df["low"],
            close=close_series,
            length=self.config.atr_length,
        )

        frames = [
            close_series.rename("close"),
            ema_fast.rename("ema_fast"),
            ema_slow.rename("ema_slow"),
            macd_df.rename(columns={
                macd_columns[0]: "macd",
                macd_columns[1]: "macd_signal",
                macd_columns[2]: "macd_hist",
            }),
            rsi.rename("rsi"),
            atr.rename("atr"),
        ]

        indicator_df = pd.concat(frames, axis=1)
        indicator_df = indicator_df.dropna()
        return indicator_df
