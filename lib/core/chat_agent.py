import json
from datetime import datetime, timedelta, timezone
from typing import Any, cast

from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.tools import StructuredTool
from langchain_openai import ChatOpenAI
from pydantic import SecretStr
from structlog.stdlib import AsyncBoundLogger

from lib.core.cal_client import CalClient
from lib.core.openai_client import OpenAIClient


class ChatAgent:
    """
    An agent that can manage conversations and schedule meetings using tools.
    It dynamically generates tools from a CalClient instance.
    """

    def __init__(
        self,
        openai_client: OpenAIClient,
        cal_client: CalClient,
    ) -> None:
        self.openai_client = openai_client
        self.cal_client = cal_client
        self.sessions: dict[str, list[BaseMessage]] = {}

        self.llm = ChatOpenAI(
            model="gpt-4-turbo",
            temperature=0,
            api_key=SecretStr(self.openai_client.client.api_key),
            base_url=str(self.openai_client.client.base_url),
        )

    def _create_tools(self, logger: AsyncBoundLogger) -> list[StructuredTool]:
        """
        Dynamically creates LangChain tools by introspecting the client methods
        """
        return self.cal_client.get_tools(agent=self, logger=logger)

    def _create_agent_executor(self, logger: AsyncBoundLogger) -> AgentExecutor:
        tools = self._create_tools(logger)
        current_time = datetime.now(timezone.utc)
        current_date = current_time.strftime("%Y-%m-%d")
        tomorrow_date = (current_time + timedelta(days=1)).strftime("%Y-%m-%d")
        system_message = (
            "You are a world class personal assistant for scheduling meetings. "
            "You always treat user with respect and kindness. "
            "If the user requests you to do anything other than managing "
            "meetings, respectfully decline. "
            "Always keep your answers concise at any cost.\n"
            "Users can - View all meetings, schedule a new meeting, "
            "cancel one or all meetings, reschedule a meeting.\n"
            f"Current UTC time: {current_time.isoformat()}.\n"
            f"Today's date: {current_date}\n"
            f"Tomorrow's date: {tomorrow_date}\n"
            "You must schedule meetings for a future time. "
            "When the user says 'tomorrow', use the tomorrow date above. "
            "Always convert times to UTC format for API calls."
        )
        prompt = ChatPromptTemplate.from_messages(
            [
                ("system", system_message),
                MessagesPlaceholder(variable_name="chat_history"),
                ("human", "{input}"),
                MessagesPlaceholder(variable_name="agent_scratchpad"),
            ]
        )
        agent = create_tool_calling_agent(self.llm, tools, prompt)
        return AgentExecutor(agent=agent, tools=tools, verbose=True)

    async def open_session(
        self, session_id: str, logger: AsyncBoundLogger
    ) -> list[BaseMessage]:
        """
        Retrieves an existing session history or creates a new one.
        """
        if session_id not in self.sessions:
            await logger.info("Creating new session", session_id=session_id)
            self.sessions[session_id] = []
        return self.sessions[session_id]

    async def get_response(
        self, session_id: str, message: str, logger: AsyncBoundLogger
    ) -> str:
        history = await self.open_session(session_id, logger)
        agent_executor = self._create_agent_executor(logger)
        await logger.info(
            "Invoking agent", user_message=message, session_id=session_id
        )
        response = await agent_executor.ainvoke(
            {"input": message, "chat_history": history}
        )
        output = cast(str, response.get("output", "Not sure how to help."))

        history.append(HumanMessage(content=message))
        history.append(AIMessage(content=output))
        return output

    async def close_session(
        self, session_id: str, logger: AsyncBoundLogger
    ) -> None:
        if session_id in self.sessions:
            del self.sessions[session_id]
            await logger.info("Closed session", session_id=session_id)

    async def _run_tool(
        self, tool_name: str, logger: AsyncBoundLogger, **kwargs: Any
    ) -> str:
        """
        Single dispatch method to run any tool by its name.
        """
        await logger.debug(
            "Agent dispatching tool", tool_name=tool_name, args=kwargs
        )
        cal_method = getattr(self.cal_client, tool_name)
        result = await cal_method(logger=logger, **kwargs)
        return json.dumps(result, indent=2)
