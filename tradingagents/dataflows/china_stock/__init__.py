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

"""China A-Share data vendor for TradingAgents.

Provides stock data, fundamentals, news, and macro indicators
for Shanghai and Shenzhen markets via mootdx and akshare.

This is a derivative work of TradingAgents by TauricResearch.
https://github.com/TauricResearch/TradingAgents
"""

from __future__ import annotations

from .mootdx_client import (
    get_stock_data as get_stock_data_mootdx,
)
from .tencent_client import (
    get_stock_data as get_stock_data_tencent,
)
from .fundamentals import (
    get_fundamentals as get_fundamentals_china,
    get_balance_sheet as get_balance_sheet_china,
    get_cashflow as get_cashflow_china,
    get_income_statement as get_income_statement_china,
)
from .news import (
    get_news as get_news_china,
    get_global_news as get_global_news_china,
    get_insider_transactions as get_insider_transactions_china,
)
from .macro import (
    get_macro_indicators as get_macro_indicators_china,
)
from .signal_data import (
    get_dragon_tiger_board as get_dragon_tiger_board_china,
    get_northbound_flow as get_northbound_flow_china,
    get_concept_blocks as get_concept_blocks_china,
    get_fund_flow as get_fund_flow_china,
    get_lockup_expiry as get_lockup_expiry_china,
    get_hot_stocks as get_hot_stocks_china,
    get_profit_forecast as get_profit_forecast_china,
    get_industry_comparison as get_industry_comparison_china,
)

# Re-export stockstats indicators (reuse yfinance implementation)
from ..y_finance import get_stock_stats_indicators_window as get_indicators_china


def get_stock_data(
    symbol: str,
    start_date: str,
    end_date: str,
):
    """Get A-Share stock data with fallback: mootdx -> tencent."""
    try:
        return get_stock_data_mootdx(symbol, start_date, end_date)
    except Exception:
        return get_stock_data_tencent(symbol, start_date, end_date)


__all__ = [
    "get_stock_data",
    "get_indicators_china",
    "get_fundamentals_china",
    "get_balance_sheet_china",
    "get_cashflow_china",
    "get_income_statement_china",
    "get_news_china",
    "get_global_news_china",
    "get_insider_transactions_china",
    "get_macro_indicators_china",
    # Signal data
    "get_dragon_tiger_board_china",
    "get_northbound_flow_china",
    "get_concept_blocks_china",
    "get_fund_flow_china",
    "get_lockup_expiry_china",
    "get_hot_stocks_china",
    "get_profit_forecast_china",
    "get_industry_comparison_china",
]
