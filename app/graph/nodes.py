import json
import time
import redis

from langchain_core.messages import SystemMessage, HumanMessage
from fastapi import Response

from LLM.GIGA_gateway import GigaChatGateway
from config_data.config import Config, load_config
from database import SQLValidator, DBGateway

from graph.states import GraphState
from utils import extract_sql
from prompts.prompts import PROMPTS
from tools.tools import export_to_csv, export_to_excel, export_to_md
from logger.logger_config import get_logger

logger = get_logger(__name__)

config: Config = load_config()

r = redis.Redis(
    host=config.redis_connector.redis_host,
    port=config.redis_connector.redis_port,
    decode_responses=True
)

tools = [export_to_csv, export_to_excel, export_to_md]
tools_dict = {
    "export_to_csv": export_to_csv,
    "export_to_excel": export_to_excel,
    "export_to_md": export_to_md
}


class Graph:
    def __init__(self):
        self.giga = GigaChatGateway()
        self.giga_with_tools = GigaChatGateway(tools=tools)
        self.sql_validator = SQLValidator()
        self.db = DBGateway()

    async def db_schema_node(self, state: GraphState):
        cached = r.get("db:schema")
        if cached:
            schema = json.loads(cached)
        else:
            schema = await self.db.get_db_schema()
            r.setex("db:schema", 3600, json.dumps(schema))
        system_message = SystemMessage(content=PROMPTS.get("SYSTEM_PROMPT").format(schema=schema))
        initial_message = state["initial_message"]
        return {"messages": [system_message, initial_message]}

    async def sql_generate_node(self, state: GraphState):
        retries_count = 0
        error = None
        while retries_count < 5:
            try:
                ai_message = await self.giga.send_to_llm(state["messages"])
                return {"messages": [ai_message]}
            except Exception as e:
                error = str(e)
                logger.error(error)
                retries_count += 1
                time.sleep(retries_count * 0.5)
        if error is not None:
            return {"final_result": Response(
                content=error
            )}

    async def sql_exec_node(self, state: GraphState):
        query = extract_sql(state["messages"][-1].content)
        valid_result, comment = await self.sql_validator(query)
        if valid_result:
            comment = await self.db.get_sql_request_result(query)
            result = str(comment)
            return {"valid_result": result}

        human_message = HumanMessage(content=comment)
        return {"messages": [human_message]}

    async def export_node(self, state: GraphState):
        valid_result = state["valid_result"]
        initial_user_message = state["initial_message"]
        system_message = SystemMessage(content=PROMPTS.get("HUMAN_EXPORT_PROMPT").format(valid_result=valid_result))
        retries_count = 0
        error = None
        while retries_count < 5:
            try:
                ai_message = await self.giga_with_tools.send_to_llm([system_message, initial_user_message])
                if not hasattr(ai_message, 'tool_calls') or not ai_message.tool_calls:
                    raise Exception('Empty list of convert tools')
                for tool_call in ai_message.tool_calls:
                    tool_name = tool_call["name"]
                    tool_args = tool_call["args"]

                    if tool_name in tools_dict:
                        result_content = await tools_dict[tool_name].ainvoke(tool_args)
                        return {"final_result": Response(
                            content=result_content["content"],
                            media_type=result_content["media_type"],
                            headers=result_content["headers"],
                        )}
                    else:
                        raise Exception("Convert Error")
            except Exception as e:
                error = str(e)
                logger.error(error)
                retries_count += 1
                time.sleep(retries_count * 0.5)
        if error is not None:
            return {"final_result": Response(
                content=error
            )}
