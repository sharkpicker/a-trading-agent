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

"""Signal data tools for China A-share specific analysis.

Provides LangChain Tool wrappers for A-share signal data: dragon-tiger boards,
northbound capital flow, concept blocks, fund flow, lockup expiry, etc.

All tools route through ``interface.route_to_vendor`` to the ``china_stock``
vendor, maintaining the same multi-vendor fallback architecture as the
standard data tools.

This is a derivative work of TradingAgents by TauricResearch.
https://github.com/TauricResearch/TradingAgents
"""

from __future__ import annotations

from langchain_core.tools import tool

from tradingagents.dataflows import interface


# ---------------------------------------------------------------------------
# Signal data tool definitions
# ---------------------------------------------------------------------------

@tool
def get_profit_forecast(symbol: str) -> str:
    """Get analyst consensus profit forecast (EPS estimates) for a China A-share stock.

    Args:
        symbol: A-share stock code (e.g. "600519" or "000001.SZ")
    """
    return interface.route_to_vendor("get_profit_forecast", symbol)


@tool
def get_hot_stocks(market: str = "A") -> str:
    """Get currently hot/trending stocks in the China A-share market with theme attribution.

    Args:
        market: Market identifier, defaults to "A" for A-shares
    """
    return interface.route_to_vendor("get_hot_stocks", market)


@tool
def get_northbound_flow(symbol: str = "", days: int = 5) -> str:
    """Get northbound capital flow (Stock Connect) data for a China A-share stock or the overall market.

    Args:
        symbol: A-share stock code (empty for overall market flow)
        days: Number of trading days to look back
    """
    return interface.route_to_vendor("get_northbound_flow", symbol, days)


@tool
def get_concept_blocks(symbol: str = "") -> str:
    """Get concept/theme block (概念板块) data for a China A-share stock or the overall market.

    Args:
        symbol: A-share stock code (empty for top concept blocks)
    """
    return interface.route_to_vendor("get_concept_blocks", symbol)


@tool
def get_fund_flow(symbol: str, days: int = 5) -> str:
    """Get individual stock capital flow breakdown (main force, retail, institutional) for a China A-share.

    Args:
        symbol: A-share stock code (e.g. "600519" or "000001.SZ")
        days: Number of trading days to look back
    """
    return interface.route_to_vendor("get_fund_flow", symbol, days)


@tool
def get_dragon_tiger_board(symbol: str, days: int = 5) -> str:
    """Get dragon-tiger board (龙虎榜) data for a China A-share stock, showing institutional and hot money seat activity.

    Args:
        symbol: A-share stock code (e.g. "600519" or "000001.SZ")
        days: Number of trading days to look back
    """
    return interface.route_to_vendor("get_dragon_tiger_board", symbol, days)


@tool
def get_lockup_expiry(symbol: str, days: int = 30) -> str:
    """Get upcoming restricted share unlock (限售股解禁) schedule for a China A-share stock.

    Args:
        symbol: A-share stock code (e.g. "600519" or "000001.SZ")
        days: Number of calendar days to look ahead
    """
    return interface.route_to_vendor("get_lockup_expiry", symbol, days)


@tool
def get_industry_comparison(symbol: str) -> str:
    """Get industry peer comparison data for a China A-share stock, including valuation, capital flow, and performance metrics.

    Args:
        symbol: A-share stock code (e.g. "600519" or "000001.SZ")
    """
    return interface.route_to_vendor("get_industry_comparison", symbol)


__all__ = [
    "get_profit_forecast",
    "get_hot_stocks",
    "get_northbound_flow",
    "get_concept_blocks",
    "get_fund_flow",
    "get_dragon_tiger_board",
    "get_lockup_expiry",
    "get_industry_comparison",
]
