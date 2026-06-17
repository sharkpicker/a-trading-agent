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

"""China A-Share fundamental data via mootdx F10."""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Annotated

from ..errors import NoMarketDataError
from ..symbol_utils import normalize_symbol, parse_china_symbol

logger = logging.getLogger(__name__)


def get_fundamentals(
    ticker: Annotated[str, "ticker symbol of the company"],
    curr_date: Annotated[str, "current date (not used for china stock)"] = None
):
    """Get A-Share company fundamentals via mootdx F10.

    Returns Label: Value text with header, matching yfinance format.
    """
    canonical = normalize_symbol(ticker)
    code, suffix = parse_china_symbol(canonical)

    try:
        from mootdx import finance

        client = finance.F10()
        profile = client.company_info(symbol=code)
        indicators = client.financial_indicator(symbol=code)

        # Map Chinese fields to standard English labels (matching yfinance)
        fields = [
            ("Name", profile.get("公司简称") or profile.get("股票简称")),
            ("Sector", profile.get("所属行业")),
            ("Industry", profile.get("主营业务")),
            ("Market Cap", indicators.get("总市值")),
            ("PE Ratio (TTM)", indicators.get("市盈率")),
            ("PB Ratio", indicators.get("市净率")),
            ("EPS (TTM)", indicators.get("每股收益")),
            ("Revenue (TTM)", indicators.get("营业收入")),
            ("Net Income", indicators.get("净利润")),
            ("Profit Margin", indicators.get("销售毛利率")),
            ("Return on Equity", indicators.get("净资产收益率")),
            ("Debt to Equity", indicators.get("资产负债率")),
            ("Current Ratio", indicators.get("流动比率")),
            ("Book Value", indicators.get("每股净资产")),
        ]

        lines = []
        for label, value in fields:
            if value is not None and str(value).strip():
                lines.append(f"{label}: {value}")

        if not lines:
            raise NoMarketDataError(ticker, canonical, "no fundamental fields returned")

        header = f"# Company Fundamentals for {canonical}\n"
        header += f"# Data retrieved on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"

        return header + "\n".join(lines)

    except NoMarketDataError:
        raise
    except Exception as e:
        logger.warning("mootdx F10 fundamentals failed for %s: %s", ticker, e)
        return f"Error retrieving fundamentals for {ticker}: {str(e)}"


def get_balance_sheet(
    ticker: Annotated[str, "ticker symbol of the company"],
    freq: Annotated[str, "frequency of data: 'annual' or 'quarterly'"] = "quarterly",
    curr_date: Annotated[str, "current date in YYYY-MM-DD format"] = None
):
    """Get A-Share balance sheet via mootdx F10."""
    canonical = normalize_symbol(ticker)
    code, suffix = parse_china_symbol(canonical)

    try:
        from mootdx import finance

        client = finance.F10()
        data = client.balance_sheet(symbol=code)

        if data.empty:
            raise NoMarketDataError(ticker, canonical, "no balance sheet data")

        csv_string = data.to_csv()

        header = f"# Balance Sheet data for {canonical} ({freq})\n"
        header += f"# Data retrieved on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"

        return header + csv_string

    except NoMarketDataError:
        raise
    except Exception as e:
        logger.warning("mootdx F10 balance sheet failed for %s: %s", ticker, e)
        return f"Error retrieving balance sheet for {ticker}: {str(e)}"


def get_cashflow(
    ticker: Annotated[str, "ticker symbol of the company"],
    freq: Annotated[str, "frequency of data: 'annual' or 'quarterly'"] = "quarterly",
    curr_date: Annotated[str, "current date in YYYY-MM-DD format"] = None
):
    """Get A-Share cash flow statement via mootdx F10."""
    canonical = normalize_symbol(ticker)
    code, suffix = parse_china_symbol(canonical)

    try:
        from mootdx import finance

        client = finance.F10()
        data = client.cash_flow(symbol=code)

        if data.empty:
            raise NoMarketDataError(ticker, canonical, "no cash flow data")

        csv_string = data.to_csv()

        header = f"# Cash Flow data for {canonical} ({freq})\n"
        header += f"# Data retrieved on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"

        return header + csv_string

    except NoMarketDataError:
        raise
    except Exception as e:
        logger.warning("mootdx F10 cash flow failed for %s: %s", ticker, e)
        return f"Error retrieving cash flow for {ticker}: {str(e)}"


def get_income_statement(
    ticker: Annotated[str, "ticker symbol of the company"],
    freq: Annotated[str, "frequency of data: 'annual' or 'quarterly'"] = "quarterly",
    curr_date: Annotated[str, "current date in YYYY-MM-DD format"] = None
):
    """Get A-Share income statement via mootdx F10."""
    canonical = normalize_symbol(ticker)
    code, suffix = parse_china_symbol(canonical)

    try:
        from mootdx import finance

        client = finance.F10()
        data = client.income_statement(symbol=code)

        if data.empty:
            raise NoMarketDataError(ticker, canonical, "no income statement data")

        csv_string = data.to_csv()

        header = f"# Income Statement data for {canonical} ({freq})\n"
        header += f"# Data retrieved on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"

        return header + csv_string

    except NoMarketDataError:
        raise
    except Exception as e:
        logger.warning("mootdx F10 income statement failed for %s: %s", ticker, e)
        return f"Error retrieving income statement for {ticker}: {str(e)}"
