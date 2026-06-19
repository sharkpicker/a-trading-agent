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

"""China A-Share news data via akshare."""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Annotated

import pandas as pd

from ..symbol_utils import normalize_symbol, parse_china_symbol
from .rate_limiter import rate_limited_retry

logger = logging.getLogger(__name__)


@rate_limited_retry("akshare", max_retries=2)
def get_news(
    ticker: Annotated[str, "ticker symbol of the company"],
    limit: Annotated[int, "max articles per ticker"] = 20
):
    """Get A-Share individual stock news via akshare."""
    canonical = normalize_symbol(ticker)
    code, _ = parse_china_symbol(canonical)

    try:
        import akshare as ak

        df = ak.stock_news_em(symbol=code)

        if df.empty:
            return f"No news found for {canonical}"

        df = df.head(limit)

        lines = []
        for _, row in df.iterrows():
            title = row.get("title", "N/A")
            content = row.get("content", "")
            pub_time = row.get("datetime", "N/A")
            lines.append(f"[{pub_time}] {title}")
            lines.append(f"  {content[:200]}...")
            lines.append("")

        header = f"# News for {canonical}\n"
        header += f"# Data retrieved on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"

        return header + "\n".join(lines)

    except Exception as e:
        logger.warning("akshare news failed for %s: %s", ticker, e)
        return f"Error retrieving news for {ticker}: {str(e)}"


@rate_limited_retry("akshare", max_retries=2)
def get_global_news(
    queries: Annotated[list[str], "search queries for global news"] = None,
    limit: Annotated[int, "max articles for global news"] = 10,
    lookback_days: Annotated[int, "macro news lookback window"] = 7,
):
    """Get China macro news via akshare."""
    if queries is None:
        queries = [
            "央行降准降息",
            "A股市场行情",
            "宏观经济数据",
            "产业政策",
        ]

    try:
        import akshare as ak

        all_news = []
        for query in queries:
            try:
                df = ak.news_cctv(query=query, days=lookback_days)
                if not df.empty:
                    all_news.append(df)
            except Exception:
                continue

        if not all_news:
            return "No global news found for the specified queries."

        combined = pd.concat(all_news).drop_duplicates()
        combined = combined.head(limit)

        lines = []
        for _, row in combined.iterrows():
            title = row.get("title", "N/A")
            content = row.get("content", "")
            pub_time = row.get("datetime", "N/A")
            lines.append(f"[{pub_time}] {title}")
            lines.append(f"  {content[:200]}...")
            lines.append("")

        header = "# Global News (China Macro)\n"
        header += f"# Data retrieved on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"

        return header + "\n".join(lines)

    except Exception as e:
        logger.warning("akshare global news failed: %s", e)
        return f"Error retrieving global news: {str(e)}"


@rate_limited_retry("akshare", max_retries=2)
def get_insider_transactions(
    ticker: Annotated[str, "ticker symbol of the company"]
):
    """Get A-Share major shareholder transactions (closest to insider data)."""
    canonical = normalize_symbol(ticker)
    code, _ = parse_china_symbol(canonical)

    try:
        import akshare as ak

        df = ak.stock_gdfx_free_holding_detail_em(symbol=code)

        if df.empty:
            return f"No insider transactions reported for symbol '{canonical}'"

        csv_string = df.to_csv()

        header = f"# Insider Transactions data for {canonical}\n"
        header += f"# Data retrieved on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"

        return header + csv_string

    except Exception as e:
        logger.warning("akshare insider transactions failed for %s: %s", ticker, e)
        return f"Error retrieving insider transactions for {ticker}: {str(e)}"
