from tradingagents.agents.utils.agent_utils import (
    get_instrument_context_from_state,
    get_language_instruction,
)


def create_conservative_debator(llm):
    def conservative_node(state) -> dict:
        risk_debate_state = state["risk_debate_state"]
        history = risk_debate_state.get("history", "")
        conservative_history = risk_debate_state.get("conservative_history", "")

        current_aggressive_response = risk_debate_state.get("current_aggressive_response", "")
        current_neutral_response = risk_debate_state.get("current_neutral_response", "")

        market_research_report = state["market_report"]
        sentiment_report = state["sentiment_report"]
        news_report = state["news_report"]
        fundamentals_report = state["fundamentals_report"]
        instrument_context = get_instrument_context_from_state(state)

        trader_decision = state["trader_investment_plan"]

        # A-Share specific reports
        policy_report = state.get("policy_report", "")
        hot_money_report = state.get("hot_money_report", "")
        lockup_report = state.get("lockup_report", "")

        # Build A-Share framework if reports exist
        ashare_framework = ""
        ashare_resources = ""
        if policy_report or hot_money_report or lockup_report:
            ashare_framework = (
                "\nA-Share Conservative Framework - emphasize these China-specific downside risks:\n"
                "- T+1 Settlement Lock: Any position taken today CANNOT be exited until tomorrow. "
                "If the stock gaps down at open, losses are locked in with no recourse.\n"
                "- Daily Price Limit Trap: If a stock hits limit-down (main board -10%, STAR/ChiNext -20%), "
                "sell orders cannot execute - you are trapped. Multiple consecutive limit-downs can cause "
                "catastrophic losses with no ability to exit.\n"
                "- Lockup Expiry Overhang: Large lockup expiries create massive potential sell pressure.\n"
                "- Policy Reversal Risk: A-shares are a policy market. What the government gives, "
                "it can take away overnight.\n"
                "- Hot Money Exit Risk: Hot money moves fast in both directions. Today's limit-up star "
                "is tomorrow's limit-down casualty.\n"
                "- Valuation Discipline: PE > 50x with PEG > 2 is speculative territory.\n"
                "- ST/Delisting Risk: For companies with consecutive losses, ST designation triggers "
                "narrow price limits and institutional forced selling.\n\n"
            )
            ashare_resources = (
                f"\nPolicy Analysis Report: {policy_report}\n"
                f"Hot Money / Capital Flow Report: {hot_money_report}\n"
                f"Lockup Expiry / Insider Reduction Report: {lockup_report}\n"
            )

        prompt = f"""As the Conservative Risk Analyst, your primary objective is to protect assets, minimize volatility, and ensure steady, reliable growth. You prioritize stability, security, and risk mitigation, carefully assessing potential losses, economic downturns, and market volatility. When evaluating the trader's decision or plan, critically examine high-risk elements, pointing out where the decision may expose the firm to undue risk and where more cautious alternatives could secure long-term gains. Here is the trader's decision:
{ashare_framework}

{trader_decision}

Your task is to actively counter the arguments of the Aggressive and Neutral Analysts, highlighting where their views may overlook potential threats or fail to prioritize sustainability. Respond directly to their points, drawing from the following data sources to build a convincing case for a low-risk approach adjustment to the trader's decision:

{instrument_context}
Market Research Report: {market_research_report}
Social Media Sentiment Report: {sentiment_report}
Latest World Affairs Report: {news_report}
Company Fundamentals Report: {fundamentals_report}
{ashare_resources}
Here is the current conversation history: {history} Here is the last response from the aggressive analyst: {current_aggressive_response} Here is the last response from the neutral analyst: {current_neutral_response}. If there are no responses from the other viewpoints yet, present your own argument based on the available data.

Engage by questioning their optimism and emphasizing the potential downsides they may have overlooked. Address each of their counterpoints to showcase why a conservative stance is ultimately the safest path for the firm's assets. Focus on debating and critiquing their arguments to demonstrate the strength of a low-risk strategy over their approaches. Output conversationally as if you are speaking without any special formatting.""" + get_language_instruction()

        response = llm.invoke(prompt)

        argument = f"Conservative Analyst: {response.content}"

        new_risk_debate_state = {
            "history": history + "\n" + argument,
            "aggressive_history": risk_debate_state.get("aggressive_history", ""),
            "conservative_history": conservative_history + "\n" + argument,
            "neutral_history": risk_debate_state.get("neutral_history", ""),
            "latest_speaker": "Conservative",
            "current_aggressive_response": risk_debate_state.get(
                "current_aggressive_response", ""
            ),
            "current_conservative_response": argument,
            "current_neutral_response": risk_debate_state.get(
                "current_neutral_response", ""
            ),
            "count": risk_debate_state["count"] + 1,
        }

        return {"risk_debate_state": new_risk_debate_state}

    return conservative_node
