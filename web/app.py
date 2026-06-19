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

"""Streamlit Web UI for TradingAgents.

Provides a browser-based interface for running stock analysis with
support for both US stocks and China A-shares.

This is a derivative work of TradingAgents by TauricResearch.
https://github.com/TauricResearch/TradingAgents

Usage:
    streamlit run web/app.py
"""

from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

import streamlit as st

# Ensure project root is on path
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from tradingagents.default_config import DEFAULT_CONFIG
from tradingagents.dataflows.config import set_config
from tradingagents.dataflows.symbol_utils import is_china_stock

# Page config
st.set_page_config(
    page_title="TradingAgents - AI Stock Analysis",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS for dark theme
st.markdown(
    """
    <style>
    .main { background-color: #1a1a2e; }
    .stTextInput, .stSelectbox, .stDateInput {
        background-color: #16213e;
    }
    .report-card {
        background-color: #16213e;
        border-radius: 10px;
        padding: 20px;
        margin-bottom: 15px;
        border: 1px solid #0f3460;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    .stTabs [data-baseweb="tab"] {
        background-color: #16213e;
        border-radius: 8px 8px 0 0;
        padding: 10px 20px;
    }
    h1, h2, h3 {
        color: #e94560;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# Session state initialization
if "status" not in st.session_state:
    st.session_state.status = "idle"  # idle, running, complete, error
if "result" not in st.session_state:
    st.session_state.result = None
if "error" not in st.session_state:
    st.session_state.error = None
if "history" not in st.session_state:
    st.session_state.history = []


def get_default_config() -> dict[str, Any]:
    """Get configuration from environment variables with defaults."""
    config = DEFAULT_CONFIG.copy()

    # Allow environment variable overrides
    config["llm_provider"] = os.getenv("TRADINGAGENTS_LLM_PROVIDER", config["llm_provider"])
    config["quick_think_llm"] = os.getenv("TRADINGAGENTS_QUICK_MODEL", config["quick_think_llm"])
    config["deep_think_llm"] = os.getenv("TRADINGAGENTS_DEEP_MODEL", config["deep_think_llm"])
    config["backend_url"] = os.getenv("TRADINGAGENTS_BACKEND_URL", config.get("backend_url", ""))

    return config


def detect_analysts(symbol: str) -> list[str]:
    """Auto-select analysts based on symbol type."""
    base_analysts = ["market", "social", "news", "fundamentals"]
    if is_china_stock(symbol):
        base_analysts.extend(["policy", "hot_money", "lockup"])
    return base_analysts


def run_analysis(symbol: str, trade_date: str, selected_analysts: list[str], config: dict):
    """Run the TradingAgents analysis pipeline."""
    from tradingagents.graph.trading_graph import TradingAgentsGraph

    set_config(config)

    graph = TradingAgentsGraph(
        selected_analysts=selected_analysts,
        config=config,
    )

    final_state, signal = graph.propagate(symbol, trade_date)
    return final_state, signal


# ---- Sidebar ----
with st.sidebar:
    st.title("TradingAgents")
    st.caption("AI-Powered Stock Analysis")
    st.divider()

    # LLM Provider settings
    st.subheader("LLM Settings")
    provider = st.selectbox(
        "Provider",
        ["openai", "google", "anthropic", "ollama", "minimax"],
        index=0,
        key="provider",
    )

    quick_model = st.text_input(
        "Quick Model",
        value=os.getenv("TRADINGAGENTS_QUICK_MODEL", "gpt-4o-mini"),
        key="quick_model",
    )
    deep_model = st.text_input(
        "Deep Model",
        value=os.getenv("TRADINGAGENTS_DEEP_MODEL", "gpt-4o"),
        key="deep_model",
    )
    backend_url = st.text_input(
        "Backend URL (optional)",
        value=os.getenv("TRADINGAGENTS_BACKEND_URL", ""),
        key="backend_url",
    )

    st.divider()

    # History
    st.subheader("History")
    if st.session_state.history:
        for entry in st.session_state.history[-5:]:
            st.markdown(f"**{entry['symbol']}** ({entry['date']}) → {entry['signal']}")
    else:
        st.caption("No analysis history yet.")

    if st.button("Clear History"):
        st.session_state.history = []
        st.rerun()


# ---- Main Content ----
st.title("AI Stock Analysis")

col1, col2 = st.columns([2, 1])

with col1:
    symbol = st.text_input(
        "Stock Symbol / Code",
        placeholder="e.g. AAPL, 600519, 000001.SZ",
        key="symbol_input",
    )

with col2:
    trade_date = st.date_input(
        "Trade Date",
        value=datetime.now().date(),
        max_value=datetime.now().date(),
        key="trade_date_input",
    )

# Detect symbol type and show info
if symbol:
    if is_china_stock(symbol):
        st.info(f"A-Share detected: {symbol}. Policy, Hot Money, and Lockup analysts will be enabled.")
        default_analysts = detect_analysts(symbol)
    else:
        st.info(f"US/Other stock: {symbol}. Standard analysts will be used.")
        default_analysts = detect_analysts(symbol)
else:
    default_analysts = ["market", "social", "news", "fundamentals"]

# Analyst selection (expandable)
with st.expander("Select Analysts", expanded=False):
    all_analysts = {
        "market": "Market Analyst (Technical)",
        "social": "Sentiment Analyst",
        "news": "News Analyst",
        "fundamentals": "Fundamentals Analyst",
        "policy": "Policy Analyst (A-Share)",
        "hot_money": "Hot Money Tracker (A-Share)",
        "lockup": "Lockup Watcher (A-Share)",
    }
    selected = []
    cols = st.columns(4)
    for i, (key, label) in enumerate(all_analysts.items()):
        with cols[i % 4]:
            checked = st.checkbox(label, value=key in default_analysts, key=f"analyst_{key}")
            if checked:
                selected.append(key)

# Run button
run_clicked = st.button(
    "Run Analysis",
    type="primary",
    disabled=st.session_state.status == "running",
    use_container_width=True,
)

if run_clicked and symbol:
    config = get_default_config()
    config["llm_provider"] = provider
    config["quick_think_llm"] = quick_model
    config["deep_think_llm"] = deep_model
    if backend_url:
        config["backend_url"] = backend_url

    st.session_state.status = "running"
    st.session_state.error = None

    with st.spinner(f"Analyzing {symbol}... This may take several minutes."):
        try:
            final_state, signal = run_analysis(
                symbol,
                trade_date.strftime("%Y-%m-%d"),
                selected,
                config,
            )
            st.session_state.result = final_state
            st.session_state.signal = signal
            st.session_state.status = "complete"

            # Add to history
            st.session_state.history.append({
                "symbol": symbol,
                "date": trade_date.strftime("%Y-%m-%d"),
                "signal": signal,
            })

        except Exception as e:
            st.session_state.error = str(e)
            st.session_state.status = "error"

# Display results
if st.session_state.status == "error":
    st.error(f"Analysis failed: {st.session_state.error}")

elif st.session_state.status == "complete" and st.session_state.result:
    result = st.session_state.result
    signal = st.session_state.signal

    # Signal banner
    signal_color = {
        "Buy": "🟢",
        "Overweight": "🟢",
        "Hold": "🟡",
        "Underweight": "🟠",
        "Sell": "🔴",
    }
    emoji = signal_color.get(signal, "⚪")
    st.markdown(f"## {emoji} Final Signal: **{signal}**")

    # Tabbed report display
    tabs = st.tabs([
        "Final Decision",
        "Market",
        "Sentiment",
        "News",
        "Fundamentals",
        "Policy",
        "Hot Money",
        "Lockup",
        "Debate",
    ])

    with tabs[0]:
        st.markdown("### Portfolio Manager Decision")
        st.markdown(result.get("final_trade_decision", "N/A"))

        st.markdown("### Trader Proposal")
        st.markdown(result.get("trader_investment_plan", "N/A"))

    with tabs[1]:
        st.markdown("### Market Analysis Report")
        st.markdown(result.get("market_report", "Not available."))

    with tabs[2]:
        st.markdown("### Sentiment Analysis Report")
        st.markdown(result.get("sentiment_report", "Not available."))

    with tabs[3]:
        st.markdown("### News Analysis Report")
        st.markdown(result.get("news_report", "Not available."))

    with tabs[4]:
        st.markdown("### Fundamentals Analysis Report")
        st.markdown(result.get("fundamentals_report", "Not available."))

    with tabs[5]:
        report = result.get("policy_report", "")
        if report:
            st.markdown("### Policy Analysis Report")
            st.markdown(report)
        else:
            st.info("Policy analysis not available (enable 'policy' analyst for A-shares).")

    with tabs[6]:
        report = result.get("hot_money_report", "")
        if report:
            st.markdown("### Hot Money / Capital Flow Report")
            st.markdown(report)
        else:
            st.info("Hot money analysis not available (enable 'hot_money' analyst for A-shares).")

    with tabs[7]:
        report = result.get("lockup_report", "")
        if report:
            st.markdown("### Lockup / Insider Reduction Report")
            st.markdown(report)
        else:
            st.info("Lockup analysis not available (enable 'lockup' analyst for A-shares).")

    with tabs[8]:
        inv_state = result.get("investment_debate_state", {})
        risk_state = result.get("risk_debate_state", {})

        st.markdown("### Investment Debate")
        st.markdown(inv_state.get("history", "No debate history."))

        st.markdown("### Risk Debate")
        st.markdown(risk_state.get("history", "No debate history."))

elif st.session_state.status == "idle":
    st.markdown(
        """
        ### Welcome to TradingAgents

        Enter a stock symbol above and click **Run Analysis** to start.

        **Supported inputs:**
        - US stocks: `AAPL`, `TSLA`, `NVDA`
        - A-shares: `600519`, `000001.SZ`, `300750.SZ`

        **Features:**
        - 7 analyst roles (4 standard + 3 A-share specific)
        - Bull/Bear debate with A-share market frameworks
        - Risk management debate with A-share trading constraints
        - Data quality gate for report validation
        """
    )
