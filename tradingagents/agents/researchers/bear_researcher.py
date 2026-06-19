from tradingagents.agents.utils.agent_utils import (
    get_instrument_context_from_state,
    get_language_instruction,
)


def create_bear_researcher(llm):
    def bear_node(state) -> dict:
        investment_debate_state = state["investment_debate_state"]
        history = investment_debate_state.get("history", "")
        bear_history = investment_debate_state.get("bear_history", "")

        current_response = investment_debate_state.get("current_response", "")
        market_research_report = state["market_report"]
        sentiment_report = state["sentiment_report"]
        news_report = state["news_report"]
        fundamentals_report = state["fundamentals_report"]
        instrument_context = get_instrument_context_from_state(state)
        asset_type = state.get("asset_type", "stock")
        target_label = "stock" if asset_type == "stock" else "asset"
        fundamentals_label = (
            "Company fundamentals report"
            if asset_type == "stock"
            else "Asset fundamentals report (may be unavailable for crypto)"
        )

        # A-Share specific reports (may be empty for non-A-share tickers)
        policy_report = state.get("policy_report", "")
        hot_money_report = state.get("hot_money_report", "")
        lockup_report = state.get("lockup_report", "")
        data_quality_summary = state.get("data_quality_summary", "")

        # Build A-Share specific framework section if reports are available
        ashare_framework = ""
        ashare_resources = ""
        if policy_report or hot_money_report or lockup_report:
            ashare_framework = (
                "\nA-Share Bear Framework - prioritize these China-specific risk factors:\n"
                "- Policy Headwinds: Sudden regulatory crackdowns (e.g. industry rectification, "
                "antitrust), CSRC window guidance, sector-wide trading restrictions, or political risk signals\n"
                "- Lockup & Insider Selling: Upcoming lockup expiry dates with large overhang, "
                "controlling shareholders in pre-disclosure reduction windows, equity pledge liquidation risk\n"
                "- Hot Money Withdrawal: Volume divergence after limit-ups, declining limit-up board count, "
                "sector rotation moving away from this theme\n"
                "- Valuation Bubble: PE far above 30x A-share growth anchor with EPS unable to digest "
                "within 3 years, PEG > 2 indicating overpriced growth, retail-driven speculative premium\n"
                "- T+1 Trap: After a sharp rally, buyers today cannot exit until tomorrow - if sentiment "
                "reverses overnight or a gap-down opens, losses are locked in\n"
                "- Northbound Retreat: Net outflow from Stock Connect signals foreign institutions "
                "reducing exposure\n\n"
            )
            ashare_resources = (
                f"Policy analysis report: {policy_report}\n"
                f"Hot money / capital flow report: {hot_money_report}\n"
                f"Lockup expiry / insider reduction report: {lockup_report}\n"
            )
            if data_quality_summary:
                ashare_resources += (
                    f"Data quality assessment: {data_quality_summary}\n"
                    "If the data quality assessment flags any report as low-confidence "
                    "(grade C/D/F), reduce your reliance on that report and note the "
                    "data limitation in your argument.\n"
                )

        prompt = f"""You are a Bear Analyst making the case against investing in the {target_label}. Your goal is to present a well-reasoned argument emphasizing risks, challenges, and negative indicators. Leverage the provided research and data to highlight potential downsides and counter bullish arguments effectively.
{ashare_framework}
Key points to focus on:

- Risks and Challenges: Highlight factors like market saturation, financial instability, or macroeconomic threats that could hinder the stock's performance.
- Competitive Weaknesses: Emphasize vulnerabilities such as weaker market positioning, declining innovation, or threats from competitors.
- Negative Indicators: Use evidence from financial data, market trends, or recent adverse news to support your position.
- Bull Counterpoints: Critically analyze the bull argument with specific data and sound reasoning, exposing weaknesses or over-optimistic assumptions.
- Engagement: Present your argument in a conversational style, directly engaging with the bull analyst's points and debating effectively rather than simply listing facts.

Resources available:

{instrument_context}
Market research report: {market_research_report}
Social media sentiment report: {sentiment_report}
Latest world affairs news: {news_report}
{fundamentals_label}: {fundamentals_report}
{ashare_resources}
Conversation history of the debate: {history}
Last bull argument: {current_response}
Use this information to deliver a compelling bear argument, refute the bull's claims, and engage in a dynamic debate that demonstrates the risks and weaknesses of investing in the {target_label}.
""" + get_language_instruction()

        response = llm.invoke(prompt)

        argument = f"Bear Analyst: {response.content}"

        new_investment_debate_state = {
            "history": history + "\n" + argument,
            "bear_history": bear_history + "\n" + argument,
            "bull_history": investment_debate_state.get("bull_history", ""),
            "current_response": argument,
            "count": investment_debate_state["count"] + 1,
        }

        return {"investment_debate_state": new_investment_debate_state}

    return bear_node
