"""Technical indicator calculations used by the orchestrator."""

from __future__ import annotations

from dataclasses import asdict
from typing import Any, Dict, Iterable

import numpy as np
import pandas as pd

from src.exchanges.base import OHLCV


def _ema(series: pd.Series, span: int) -> pd.Series:
    return series.ewm(span=span, adjust=False).mean()


def _macd(series: pd.Series) -> pd.DataFrame:
    ema12 = _ema(series, 12)
    ema26 = _ema(series, 26)
    macd_line = ema12 - ema26
    signal = _ema(macd_line, 9)
    hist = macd_line - signal
    return pd.DataFrame({"macd": macd_line, "signal": signal, "hist": hist})


def _rsi(series: pd.Series, period: int) -> pd.Series:
    delta = series.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.ewm(alpha=1 / period, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1 / period, adjust=False).mean()
    rs = avg_gain / avg_loss.replace({0: np.nan})
    rsi = 100 - (100 / (1 + rs))
    return rsi.fillna(50.0)


def _atr(df: pd.DataFrame, period: int) -> pd.Series:
    high_low = df["high"] - df["low"]
    high_close = (df["high"] - df["close"].shift()).abs()
    low_close = (df["low"] - df["close"].shift()).abs()
    true_range = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
    return true_range.rolling(window=period, min_periods=1).mean()


class TechnicalIndicators:
    """Calculate technical indicators for intraday and higher timeframes."""

    def calculate(self, candles_3m: Iterable[OHLCV], candles_4h: Iterable[OHLCV]) -> Dict[str, Any]:
        intraday_df = self._to_dataframe(candles_3m)
        higher_df = self._to_dataframe(candles_4h)

        intraday = self._intraday_metrics(intraday_df)
        longer_term = self._longer_term_metrics(higher_df)

        return {"intraday": intraday, "longer_term": longer_term}

    def _to_dataframe(self, candles: Iterable[OHLCV]) -> pd.DataFrame:
        records = [asdict(candle) for candle in candles]
        if not records:
            return pd.DataFrame(columns=["timestamp", "open", "high", "low", "close", "volume"])
        df = pd.DataFrame(records)
        df.sort_values("timestamp", inplace=True)
        df.reset_index(drop=True, inplace=True)
        return df

    def _intraday_metrics(self, df: pd.DataFrame) -> Dict[str, Any]:
        if df.empty:
            return {}

        close = df["close"]
        ema20 = _ema(close, 20)
        macd_df = _macd(close)
        rsi7 = _rsi(close, 7)
        rsi14 = _rsi(close, 14)

        return {
            "current_price": float(close.iloc[-1]),
            "current_ema20": float(ema20.iloc[-1]),
            "current_macd": float(macd_df["macd"].iloc[-1]),
            "current_rsi_7": float(rsi7.iloc[-1]),
            "prices": close.tail(20).round(4).tolist(),
            "ema_20": ema20.tail(20).round(4).tolist(),
            "macd_series": macd_df["macd"].tail(20).round(4).tolist(),
            "rsi_7_series": rsi7.tail(20).round(2).tolist(),
            "rsi_14_series": rsi14.tail(20).round(2).tolist(),
        }

    def _longer_term_metrics(self, df: pd.DataFrame) -> Dict[str, Any]:
        if df.empty:
            return {}

        close = df["close"]
        ema20 = _ema(close, 20)
        ema50 = _ema(close, 50)
        macd_df = _macd(close)
        rsi14 = _rsi(close, 14)
        atr3 = _atr(df, 3)
        atr14 = _atr(df, 14)

        return {
            "ema_20": float(ema20.iloc[-1]),
            "ema_50": float(ema50.iloc[-1]),
            "macd_series": macd_df["macd"].tail(20).round(4).tolist(),
            "rsi_14_series": rsi14.tail(20).round(2).tolist(),
            "atr_3": float(atr3.iloc[-1]),
            "atr_14": float(atr14.iloc[-1]),
            "current_volume": float(df["volume"].iloc[-1]),
            "avg_volume": float(df["volume"].rolling(window=20, min_periods=1).mean().iloc[-1]),
        }


__all__ = ["TechnicalIndicators"]
