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

"""Lockup Watcher: monitors restricted share unlock schedules and insider
reduction activity in China A-share markets.

This is a derivative work of TradingAgents by TauricResearch.
https://github.com/TauricResearch/TradingAgents
"""

from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

from tradingagents.agents.utils.agent_utils import (
    get_instrument_context_from_state,
    get_language_instruction,
)


def create_lockup_watcher(llm):
    def lockup_watcher_node(state):
        current_date = state["trade_date"]
        instrument_context = get_instrument_context_from_state(state)

        system_message = (
            "You are a Lockup & Insider Reduction Analyst specializing in China A-share markets. "
            "Your task is to monitor and analyze restricted share unlock schedules (限售股解禁) "
            "and insider reduction activity (股东减持) around the target stock.\n\n"
            "Focus areas:\n"
            "1. **Lockup Expiry Calendar (解禁日历)**: Identify upcoming lockup expiry dates, "
            "the volume of shares being unlocked, and the proportion relative to total float.\n"
            "2. **Reduction Pressure Rating (减持压力评级)**: Assess the likelihood and magnitude "
            "of insider selling based on lockup size, historical patterns, and current price levels.\n"
            "3. **Controlling Shareholder Activity**: Track pre-disclosure reduction plans "
            "(预披露减持) by controlling shareholders and major shareholders.\n"
            "4. **Equity Pledge Risk (股权质押风险)**: Monitor equity pledge ratios and "
            "potential forced liquidation triggers.\n"
            "5. **Secondary Offering Impact**: Evaluate any planned secondary offerings "
            "(定增/配股) and their dilution effects.\n\n"
            "Use the available signal data tools to gather this information. Provide specific "
            "dates, volumes, and risk assessments.\n\n"
            "Write a comprehensive lockup/reduction risk analysis report."
            + " Make sure to append a Markdown table at the end of the report to organize "
            "key lockup and reduction data."
            + get_language_instruction()
        )

        prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    "You are a helpful AI assistant, collaborating with other assistants."
                    " Use the provided tools to progress towards answering the question."
                    " If you are unable to fully answer, that's OK; another assistant with different tools"
                    " will help where you left off. Execute what you can to make progress."
                    " If you or any other assistant has the FINAL TRANSACTION PROPOSAL: **BUY/HOLD/SELL** or deliverable,"
                    " prefix your response with FINAL TRANSACTION PROPOSAL: **BUY/HOLD/SELL** so the team knows to stop."
                    " You have access to the following tools: {tool_names}.\n{system_message}"
                    "For your reference, the current date is {current_date}. {instrument_context}",
                ),
                MessagesPlaceholder(variable_name="messages"),
            ]
        )

        # Lockup watcher uses signal data tools
        from tradingagents.agents.utils.signal_data_tools import (
            get_lockup_expiry,
            get_hot_stocks,
        )
        tools = [get_lockup_expiry, get_hot_stocks]

        prompt = prompt.partial(system_message=system_message)
        prompt = prompt.partial(tool_names=", ".join([tool.name for tool in tools]))
        prompt = prompt.partial(current_date=current_date)
        prompt = prompt.partial(instrument_context=instrument_context)

        chain = prompt | llm.bind_tools(tools)

        result = chain.invoke(state["messages"])

        report = ""
        if len(result.tool_calls) == 0:
            report = result.content

        return {
            "messages": [result],
            "lockup_report": report,
        }

    return lockup_watcher_node
