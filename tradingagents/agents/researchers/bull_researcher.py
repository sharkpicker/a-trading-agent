from tradingagents.agents.utils.agent_utils import (
    get_instrument_context_from_state,
    get_language_instruction,
)


def create_bull_researcher(llm):
    def bull_node(state) -> dict:
        investment_debate_state = state["investment_debate_state"]
        history = investment_debate_state.get("history", "")
        bull_history = investment_debate_state.get("bull_history", "")

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
                "\nA-Share Bull Framework - prioritize these China-specific bullish catalysts:\n"
                "- Policy Tailwinds: Government subsidies, industry support policies "
                "(e.g. 'specialized and sophisticated' enterprises, national strategic sectors), "
                "favorable regulatory signals from CSRC/State Council\n"
                "- Northbound Capital: Sustained net inflow from Hong Kong Stock Connect "
                "indicates foreign institutional conviction\n"
                "- Hot Money Momentum: Consecutive limit-ups with volume confirmation, "
                "strong theme attribution, sector rotation just beginning\n"
                "- Valuation Growth Story: Use forward PE, PEG, and PE digestion timeframe "
                "(30x anchor for A-share growth stocks) to argue the current premium is "
                "justified by earnings trajectory\n"
                "- Lockup Expiry Cleared: If major lockup periods have passed or insiders "
                "are NOT reducing, this removes a key overhang\n\n"
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

        prompt = f"""You are a Bull Analyst advocating for investing in the {target_label}. Your task is to build a strong, evidence-based case emphasizing growth potential, competitive advantages, and positive market indicators. Leverage the provided research and data to address concerns and counter bearish arguments effectively.
{ashare_framework}
Key points to focus on:
- Growth Potential: Highlight the company's market opportunities, revenue projections, and scalability.
- Competitive Advantages: Emphasize factors like unique products, strong branding, or dominant market positioning.
- Positive Indicators: Use financial health, industry trends, and recent positive news as evidence.
- Bear Counterpoints: Critically analyze the bear argument with specific data and sound reasoning, addressing concerns thoroughly and showing why the bull perspective holds stronger merit.
- Engagement: Present your argument in a conversational style, engaging directly with the bear analyst's points and debating effectively rather than just listing data.

Resources available:
{instrument_context}
Market research report: {market_research_report}
Social media sentiment report: {sentiment_report}
Latest world affairs news: {news_report}
{fundamentals_label}: {fundamentals_report}
{ashare_resources}
Conversation history of the debate: {history}
Last bear argument: {current_response}
Use this information to deliver a compelling bull argument, refute the bear's concerns, and engage in a dynamic debate that demonstrates the strengths of the bull position.
""" + get_language_instruction()

        response = llm.invoke(prompt)

        argument = f"Bull Analyst: {response.content}"

        new_investment_debate_state = {
            "history": history + "\n" + argument,
            "bull_history": bull_history + "\n" + argument,
            "bear_history": investment_debate_state.get("bear_history", ""),
            "current_response": argument,
            "count": investment_debate_state["count"] + 1,
        }

        return {"investment_debate_state": new_investment_debate_state}

    return bull_node
