"""Trader: turns the Research Manager's investment plan into a concrete transaction proposal."""

from __future__ import annotations

import functools

from langchain_core.messages import AIMessage

from tradingagents.agents.schemas import TraderProposal, render_trader_proposal
from tradingagents.agents.utils.agent_utils import (
    get_instrument_context_from_state,
    get_language_instruction,
)
from tradingagents.agents.utils.structured import (
    bind_structured,
    invoke_structured_or_freetext,
)


def create_trader(llm):
    structured_llm = bind_structured(llm, TraderProposal, "Trader")

    def trader_node(state, name):
        company_name = state["company_of_interest"]
        instrument_context = get_instrument_context_from_state(state)
        investment_plan = state["investment_plan"]

        messages = [
            {
                "role": "system",
                "content": (
                    "You are a trading agent analyzing market data to make investment decisions. "
                    "Based on your analysis, provide a specific recommendation to buy, sell, or hold. "
                    "Anchor your reasoning in the analysts' reports and the research plan."
                    + get_language_instruction()
                ),
            },
            {
                "role": "user",
                "content": (
                    f"Based on a comprehensive analysis by a team of analysts, here is an investment "
                    f"plan tailored for {company_name}. {instrument_context} This plan incorporates "
                    f"insights from current technical market trends, macroeconomic indicators, and "
                    f"social media sentiment. Use this plan as a foundation for evaluating your next "
                    f"trading decision.\n\n"
                    f"Proposed Investment Plan: {investment_plan}\n\n"
                    f"Leverage these insights to make an informed and strategic decision."
                ),
            },
        ]

        # Inject A-share trading constraints if A-share specific reports exist
        state_for_constraints = state if isinstance(state, dict) else {}
        policy_report = state_for_constraints.get("policy_report", "")
        hot_money_report = state_for_constraints.get("hot_money_report", "")
        lockup_report = state_for_constraints.get("lockup_report", "")

        if policy_report or hot_money_report or lockup_report:
            ashare_constraints = (
                "\n\nIMPORTANT - A-Share Trading Constraints (must be reflected in your proposal):\n"
                "- T+1 Settlement: Positions bought today can only be sold tomorrow (next trading day).\n"
                "- Price Limits: Main board stocks have +/-10% daily limit; STAR/ChiNext have +/-20%; "
                "BJSE has +/-30%. Your target price must respect these limits.\n"
                "- Minimum Lot Size: Orders must be in multiples of 100 shares (1 lot).\n"
                "- Trading Hours: 9:30-11:30 and 13:00-15:00 Beijing time. No pre-market or after-hours.\n"
                "- ST Risk: If the stock has ST/ST* designation, daily limits are +/-5% and institutional "
                "participation is restricted.\n"
                "- Margin Trading: Only designated stocks can be traded on margin; check eligibility.\n"
                "- Consider the policy, capital flow, and lockup reports above when setting position size "
                "and timing.\n"
            )
            messages[1]["content"] += ashare_constraints

        trader_plan = invoke_structured_or_freetext(
            structured_llm,
            llm,
            messages,
            render_trader_proposal,
            "Trader",
        )

        return {
            "messages": [AIMessage(content=trader_plan)],
            "trader_investment_plan": trader_plan,
            "sender": name,
        }

    return functools.partial(trader_node, name="Trader")
