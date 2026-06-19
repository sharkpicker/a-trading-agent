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

"""Hot Money Tracker: tracks capital flows, dragon-tiger boards, and
institutional activity in China A-share markets.

This is a derivative work of TradingAgents by TauricResearch.
https://github.com/TauricResearch/TradingAgents
"""

from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

from tradingagents.agents.utils.agent_utils import (
    get_instrument_context_from_state,
    get_language_instruction,
)


def create_hot_money_tracker(llm):
    def hot_money_tracker_node(state):
        current_date = state["trade_date"]
        instrument_context = get_instrument_context_from_state(state)

        system_message = (
            "You are a Hot Money & Capital Flow Analyst specializing in China A-share markets. "
            "Your task is to track and analyze capital flows, institutional activity, and "
            "hot money (游资) behavior around the target stock.\n\n"
            "Focus areas:\n"
            "1. **Dragon-Tiger Board (龙虎榜)**: Identify institutional seats, hot money "
            "seats, and their buy/sell amounts. Track consecutive appearances.\n"
            "2. **Northbound Capital (北向资金)**: Monitor Stock Connect net inflow/outflow. "
            "Sustained buying by foreign institutions is a strong confidence signal.\n"
            "3. **Concept/Theme Blocks (概念板块)**: Identify which themes the stock belongs to "
            "and their current momentum (e.g. AI, new energy, low-altitude economy).\n"
            "4. **Individual Stock Capital Flow**: Analyze main force (主力), retail, and "
            "institutional net inflow/outflow patterns.\n"
            "5. **Industry Comparison**: Compare the stock's capital flow and performance "
            "against industry peers.\n\n"
            "Use the available signal data tools to gather this information. Provide specific "
            "data points and actionable insights about capital flow dynamics.\n\n"
            "Write a comprehensive capital flow analysis report."
            + " Make sure to append a Markdown table at the end of the report to organize "
            "key capital flow metrics."
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

        # Hot money tracker uses signal data tools
        from tradingagents.agents.utils.signal_data_tools import (
            get_dragon_tiger_board,
            get_northbound_flow,
            get_concept_blocks,
            get_fund_flow,
            get_industry_comparison,
        )
        tools = [
            get_dragon_tiger_board,
            get_northbound_flow,
            get_concept_blocks,
            get_fund_flow,
            get_industry_comparison,
        ]

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
            "hot_money_report": report,
        }

    return hot_money_tracker_node
