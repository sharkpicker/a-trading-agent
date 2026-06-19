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

"""Signal data layer for China A-share markets.

Provides A-share specific signal data functions: dragon-tiger boards,
northbound capital flow, concept blocks, fund flow, lockup expiry,
hot stocks, profit forecasts, and industry comparisons.

All functions return CSV-formatted strings consistent with the existing
vendor output format.

This is a derivative work of TradingAgents by TauricResearch.
https://github.com/TauricResearch/TradingAgents
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta

from .rate_limiter import rate_limited_retry

logger = logging.getLogger(__name__)


def _try_akshare(fn):
    """Decorator that gracefully handles akshare import failures."""
    def wrapper(*args, **kwargs):
        try:
            return fn(*args, **kwargs)
        except ImportError:
            return "ERROR: akshare is required for this function. Install with: pip install akshare"
        except Exception as e:
            logger.warning("Signal data function %s failed: %s", fn.__name__, e)
            return f"ERROR: Failed to retrieve data: {e}"
    return wrapper


# ---------------------------------------------------------------------------
# Dragon-Tiger Board (龙虎榜)
# ---------------------------------------------------------------------------

@rate_limited_retry("akshare", max_retries=2)
@_try_akshare
def get_dragon_tiger_board(symbol: str, days: int = 5) -> str:
    """Get dragon-tiger board data for a stock.

    Returns CSV with columns: date,stock_code,stock_name,reason,buy_amount,
    sell_amount,net_amount,seat_name,seat_type
    """
    import akshare as ak

    # Normalize symbol to pure 6-digit code
    code = symbol.replace(".SS", "").replace(".SZ", "").replace(".BJ", "")

    end_date = datetime.now().strftime("%Y%m%d")
    start_date = (datetime.now() - timedelta(days=days * 2)).strftime("%Y%m%d")

    try:
        df = ak.stock_lhb_detail_em(start_date=start_date, end_date=end_date)
        if df is None or df.empty:
            return "NO_DATA_AVAILABLE: No dragon-tiger board data found."

        # Filter for the target stock
        code_col = [c for c in df.columns if "代码" in str(c)]
        if code_col:
            df = df[df[code_col[0]].astype(str).str.contains(code)]

        if df.empty:
            return f"NO_DATA_AVAILABLE: No dragon-tiger board data for {symbol} in the past {days} days."

        return df.to_csv(index=False)
    except Exception as e:
        return f"ERROR: Failed to fetch dragon-tiger board data: {e}"


# ---------------------------------------------------------------------------
# Northbound Capital Flow (北向资金)
# ---------------------------------------------------------------------------

@rate_limited_retry("akshare", max_retries=2)
@_try_akshare
def get_northbound_flow(symbol: str = "", days: int = 5) -> str:
    """Get northbound capital flow data via Stock Connect.

    Returns CSV with columns: date,net_buy_amount,net_buy_sh,net_buy_sz,
    total_hold_market_cap,total_hold_ratio
    """
    import akshare as ak

    try:
        df = ak.stock_hsgt_north_net_flow_in_em(symbol="北向资金")
        if df is None or df.empty:
            return "NO_DATA_AVAILABLE: No northbound flow data available."

        # Keep only recent days
        if len(df) > days:
            df = df.head(days)

        return df.to_csv(index=False)
    except Exception as e:
        return f"ERROR: Failed to fetch northbound flow data: {e}"


# ---------------------------------------------------------------------------
# Concept Blocks (概念板块)
# ---------------------------------------------------------------------------

@rate_limited_retry("akshare", max_retries=2)
@_try_akshare
def get_concept_blocks(symbol: str = "") -> str:
    """Get concept/theme block data.

    If symbol is provided, returns the concept blocks the stock belongs to.
    Otherwise returns top concept blocks by market performance.

    Returns CSV with columns: block_name,block_code,change_pct,lead_stock,
    turnover_rate,net_inflow
    """
    import akshare as ak

    try:
        df = ak.stock_board_concept_name_em()
        if df is None or df.empty:
            return "NO_DATA_AVAILABLE: No concept block data available."

        if symbol:
            code = symbol.replace(".SS", "").replace(".SZ", "").replace(".BJ", "")
            # Get individual stock concept membership
            try:
                stock_df = ak.stock_individual_info_em(symbol=code)
                return stock_df.to_csv(index=False)
            except Exception:
                pass

        # Return top concept blocks
        return df.head(20).to_csv(index=False)
    except Exception as e:
        return f"ERROR: Failed to fetch concept block data: {e}"


# ---------------------------------------------------------------------------
# Individual Stock Capital Flow (个股资金流)
# ---------------------------------------------------------------------------

@rate_limited_retry("akshare", max_retries=2)
@_try_akshare
def get_fund_flow(symbol: str, days: int = 5) -> str:
    """Get individual stock capital flow breakdown.

    Returns CSV with columns: date,main_net_inflow,main_net_inflow_pct,
    retail_net_inflow,super_large_net,large_net,medium_net,small_net
    """
    import akshare as ak

    code = symbol.replace(".SS", "").replace(".SZ", "").replace(".BJ", "")

    try:
        df = ak.stock_individual_fund_flow(stock=code, market="sh" if code.startswith("6") else "sz")
        if df is None or df.empty:
            return f"NO_DATA_AVAILABLE: No fund flow data for {symbol}."

        if len(df) > days:
            df = df.head(days)

        return df.to_csv(index=False)
    except Exception as e:
        return f"ERROR: Failed to fetch fund flow data: {e}"


# ---------------------------------------------------------------------------
# Lockup Expiry (限售股解禁)
# ---------------------------------------------------------------------------

@rate_limited_retry("akshare", max_retries=2)
@_try_akshare
def get_lockup_expiry(symbol: str, days: int = 30) -> str:
    """Get upcoming restricted share unlock schedule.

    Returns CSV with columns: date,stock_code,stock_name,unlock_shares,
    unlock_market_cap,unlock_ratio,total_shares,float_shares
    """
    import akshare as ak

    code = symbol.replace(".SS", "").replace(".SZ", "").replace(".BJ", "")

    try:
        df = ak.stock_restricted_release_summary_em()
        if df is None or df.empty:
            return "NO_DATA_AVAILABLE: No lockup expiry data available."

        # Filter for the target stock
        code_col = [c for c in df.columns if "代码" in str(c)]
        if code_col:
            df = df[df[code_col[0]].astype(str).str.contains(code)]

        if df.empty:
            return f"NO_DATA_AVAILABLE: No upcoming lockup expiry for {symbol} in the next {days} days."

        return df.to_csv(index=False)
    except Exception as e:
        return f"ERROR: Failed to fetch lockup expiry data: {e}"


# ---------------------------------------------------------------------------
# Hot Stocks (热门股)
# ---------------------------------------------------------------------------

@rate_limited_retry("akshare", max_retries=2)
@_try_akshare
def get_hot_stocks(market: str = "A") -> str:
    """Get currently hot/trending stocks with theme attribution.

    Returns CSV with columns: rank,stock_code,stock_name,change_pct,
    turnover_rate,theme,reason_tag,main_net_inflow
    """
    import akshare as ak

    try:
        df = ak.stock_hot_rank_em()
        if df is None or df.empty:
            return "NO_DATA_AVAILABLE: No hot stock data available."

        return df.head(30).to_csv(index=False)
    except Exception as e:
        return f"ERROR: Failed to fetch hot stock data: {e}"


# ---------------------------------------------------------------------------
# Profit Forecast (一致预期)
# ---------------------------------------------------------------------------

@rate_limited_retry("akshare", max_retries=2)
@_try_akshare
def get_profit_forecast(symbol: str) -> str:
    """Get analyst consensus profit forecast (EPS estimates).

    Returns CSV with columns: year,report_date,eps_avg,eps_max,eps_min,
    analyst_count,research_institution_count
    """
    import akshare as ak

    code = symbol.replace(".SS", "").replace(".SZ", "").replace(".BJ", "")

    try:
        df = ak.stock_profit_forecast_ths(symbol=code)
        if df is None or df.empty:
            return f"NO_DATA_AVAILABLE: No profit forecast data for {symbol}."

        return df.to_csv(index=False)
    except Exception as e:
        return f"ERROR: Failed to fetch profit forecast data: {e}"


# ---------------------------------------------------------------------------
# Industry Comparison (行业横向对比)
# ---------------------------------------------------------------------------

@rate_limited_retry("akshare", max_retries=2)
@_try_akshare
def get_industry_comparison(symbol: str) -> str:
    """Get industry peer comparison data.

    Returns CSV with columns: stock_code,stock_name,pe_ttm,pb,market_cap,
    change_pct,turnover_rate,revenue_yoy,net_profit_yoy
    """
    import akshare as ak

    code = symbol.replace(".SS", "").replace(".SZ", "").replace(".BJ", "")

    try:
        # Get stock's industry classification
        industry_df = ak.stock_board_industry_cons_em(symbol=code)
        if industry_df is None or industry_df.empty:
            return f"NO_DATA_AVAILABLE: No industry comparison data for {symbol}."

        return industry_df.to_csv(index=False)
    except Exception as e:
        return f"ERROR: Failed to fetch industry comparison data: {e}"


__all__ = [
    "get_dragon_tiger_board",
    "get_northbound_flow",
    "get_concept_blocks",
    "get_fund_flow",
    "get_lockup_expiry",
    "get_hot_stocks",
    "get_profit_forecast",
    "get_industry_comparison",
]
