"""China A-Share stock data via mootdx (primary source)."""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Annotated

import pandas as pd

from ..errors import NoMarketDataError
from ..symbol_utils import normalize_symbol, parse_china_symbol

logger = logging.getLogger(__name__)


def get_stock_data(
    symbol: Annotated[str, "ticker symbol of the company"],
    start_date: Annotated[str, "Start date in yyyy-mm-dd format"],
    end_date: Annotated[str, "End date in yyyy-mm-dd format"],
):
    """Retrieve A-Share stock price data (OHLCV) via mootdx.

    Returns CSV string with header, matching yfinance format exactly.
    """
    canonical = normalize_symbol(symbol)
    code, suffix = parse_china_symbol(canonical)

    try:
        from mootdx import quotes
        from mootdx.consts import MARKET_SH, MARKET_SZ

        market_map = {".SS": MARKET_SH, ".SZ": MARKET_SZ}
        market = market_map.get(suffix, MARKET_SH)

        client = quotes.Quotes.factory(market="std")
        data = client.kline(
            symbol=code,
            market=market,
            start=start_date,
            end=end_date,
        )

        if data.empty:
            raise NoMarketDataError(
                symbol, canonical, f"no rows between {start_date} and {end_date}"
            )

        # Standardize column names to match yfinance
        column_map = {
            "date": "Date",
            "open": "Open",
            "high": "High",
            "low": "Low",
            "close": "Close",
            "vol": "Volume",
        }
        data = data.rename(columns={k: v for k, v in column_map.items() if k in data.columns})

        # Ensure required columns exist
        required = ["Date", "Open", "High", "Low", "Close", "Volume"]
        for col in required:
            if col not in data.columns:
                data[col] = 0.0 if col != "Date" else ""

        data = data[required]

        # Round prices to 2 decimal places
        for col in ["Open", "High", "Low", "Close"]:
            data[col] = data[col].round(2)

        csv_string = data.to_csv(index=False)

        label = canonical if canonical == symbol.upper() else f"{canonical} (from {symbol})"
        header = f"# Stock data for {label} from {start_date} to {end_date}\n"
        header += f"# Total records: {len(data)}\n"
        header += f"# Data retrieved on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"

        return header + csv_string

    except NoMarketDataError:
        raise
    except Exception as e:
        logger.warning("mootdx failed for %s: %s", symbol, e)
        raise
