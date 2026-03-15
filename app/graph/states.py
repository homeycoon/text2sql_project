from typing import TypedDict, Sequence, Annotated, Optional, Any

from langchain_core.messages import BaseMessage
from langgraph.graph import add_messages


class GraphState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], add_messages]
    initial_message: BaseMessage
    valid_result: Optional[str]
    final_result: Optional[Any]
