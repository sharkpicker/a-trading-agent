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

"""Policy Analyst: analyzes macro/regulatory/industrial policy impacts on A-shares.

This is a derivative work of TradingAgents by TauricResearch.
https://github.com/TauricResearch/TradingAgents
"""

from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

from tradingagents.agents.utils.agent_utils import (
    get_instrument_context_from_state,
    get_language_instruction,
)


def create_policy_analyst(llm):
    def policy_analyst_node(state):
        current_date = state["trade_date"]
        instrument_context = get_instrument_context_from_state(state)

        system_message = (
            "You are a Policy Analyst specializing in China A-share markets. "
            "Your task is to analyze the policy environment affecting the target stock "
            "across five layers:\n\n"
            "1. **Macro Policy**: Central bank (PBOC) monetary policy, fiscal stimulus, "
            "government work report priorities, GDP growth targets, MLF/LPR rate decisions.\n"
            "2. **Regulatory Policy**: CSRC regulations, IPO/delisting rules, margin "
            "trading adjustments, stock connect quota changes, window guidance (窗口指导).\n"
            "3. **Industrial Policy**: National strategic sectors (专精特新), subsidies, "
            "tax incentives, industry-specific support plans (e.g. AI, new energy, chips).\n"
            "4. **Local Policy**: Provincial/city-level incentives, free trade zone policies, "
            "local government procurement preferences.\n"
            "5. **International Policy**: Trade tensions, sanctions, cross-border capital "
            "flow policies, foreign ownership restrictions.\n\n"
            "Use the available tools to gather news and macro data. Focus on identifying "
            "policy tailwinds (positive catalysts) and policy headwinds (risks) that "
            "could materially impact the target stock's price trajectory.\n\n"
            "Write a comprehensive policy analysis report with specific, actionable insights. "
            "Rate the overall policy environment as: Favorable / Neutral / Unfavorable."
            + " Make sure to append a Markdown table at the end of the report to organize "
            "key policy factors."
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

        # Policy analyst uses news and macro tools
        from tradingagents.agents.utils.agent_utils import (
            get_news,
            get_global_news,
            get_macro_indicators,
        )
        tools = [get_news, get_global_news, get_macro_indicators]

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
            "policy_report": report,
        }

    return policy_analyst_node
