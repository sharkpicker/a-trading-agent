# Copyright 2026 sharkpicker
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""China A-Share stock data via Tencent Finance (fallback source)."""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Annotated

import pandas as pd
import requests

from ..errors import NoMarketDataError
from ..symbol_utils import normalize_symbol, parse_china_symbol
from .rate_limiter import rate_limited_retry

logger = logging.getLogger(__name__)


@rate_limited_retry("tencent", max_retries=2)
def get_stock_data(
    symbol: Annotated[str, "ticker symbol of the company"],
    start_date: Annotated[str, "Start date in yyyy-mm-dd format"],
    end_date: Annotated[str, "End date in yyyy-mm-dd format"],
):
    """Retrieve A-Share stock price data (OHLCV) via Tencent Finance API.

    Returns CSV string with header, matching yfinance format exactly.
    """
    canonical = normalize_symbol(symbol)
    code, suffix = parse_china_symbol(canonical)

    try:
        # Tencent uses exchange codes: 1=SH, 0=SZ
        exchange_code = "1" if suffix == ".SS" else "0"
        secid = f"{exchange_code}.{code}"

        params = {
            "secid": secid,
            "ut": "fa5fd1943c7b386f172d6893dbfba10b",
            "fields1": "f1,f2,f3,f4,f5,f6",
            "fields2": "f51,f52,f53,f54,f55,f56,f57,f58,f59,f60,f61",
            "klt": "101",  # daily
            "fqt": "0",    # no adjustment
            "beg": start_date.replace("-", ""),
            "end": end_date.replace("-", ""),
        }

        url = "https://push2his.eastmoney.com/api/qt/stock/kline/get"
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()
        json_data = response.json()

        if not json_data.get("data") or not json_data["data"].get("klines"):
            raise NoMarketDataError(symbol, canonical, "no data from tencent")

        klines = json_data["data"]["klines"]
        rows = []
        for line in klines:
            parts = line.split(",")
            if len(parts) >= 6:
                rows.append({
                    "Date": parts[0],
                    "Open": float(parts[1]),
                    "Close": float(parts[2]),
                    "High": float(parts[3]),
                    "Low": float(parts[4]),
                    "Volume": float(parts[5]),
                })

        if not rows:
            raise NoMarketDataError(symbol, canonical, "empty klines from tencent")

        data = pd.DataFrame(rows)
        data = data[["Date", "Open", "High", "Low", "Close", "Volume"]]

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
        logger.warning("tencent finance failed for %s: %s", symbol, e)
        raise
