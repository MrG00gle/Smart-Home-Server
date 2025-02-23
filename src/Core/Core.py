import uuid
from datetime import datetime
from langchain_core.messages import ToolMessage, BaseMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableLambda, RunnableSerializable
from langchain_ollama import ChatOllama
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import StateGraph, START
from langgraph.graph.state import CompiledStateGraph
from langgraph.prebuilt import tools_condition, ToolNode
from numpy.ma.core import append

from src.Core.Assistant import Assistant
from src.Core.State import State
from src.tools.llm_tools import get_tools

class Core:
    def __init__(self):
        self.llm = ChatOllama(model="llama3.2:3b", temperature=0.2)
        self.tools = get_tools()
        self.prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    "You are a helpful home assistant."
                    "Your name is Archi."
                    "Do not call tools unless the user explicitly requests it"
                    "If the user's request cannot be fulfilled with the provided tools, respond appropriately."
                    "\n\nCurrent user:\n<User>\n{user_info}\n</User>"
                    "\nCurrent time: {time}.",
                ),
                ("placeholder", "{messages}"),
            ]
        ).partial(time=datetime.now())
        self.config = {
            "configurable": {
                # The passenger_id is used in our flight tools to
                # fetch the user's flight information
                "passenger_id": "3442 587242",
                # Checkpoints are accessed by thread_id
                "thread_id": str(uuid.uuid4()),
            }
        }
        self.memory = MemorySaver()
        self._printed = set()
        self.assistant = Assistant(self.create_runnabe())

    def create_runnabe(self) -> RunnableSerializable[dict, BaseMessage]:
        runnable = self.prompt | self.llm.bind_tools(self.tools)
        return runnable

    # Help Utilities
    def create_tool_node_with_fallback(self, tools: list) -> dict:
        return ToolNode(tools).with_fallbacks([RunnableLambda(self._handle_tool_error)], exception_key="error")

    def _handle_tool_error(self, state) -> dict:
        error = state.get("error")
        tool_calls = state["messages"][-1].tool_calls
        return {
            "messages": [
                ToolMessage(
                    content=f"Error: {repr(error)}\n please fix your mistakes.",
                    tool_call_id=tc["id"],
                )
                for tc in tool_calls
            ]
        }

    def _print_event(self, event: dict, _printed: set, max_length=1500):
        current_state = event.get("dialog_state")
        if current_state:
            print("Currently in: ", current_state[-1])
        message = event.get("messages")
        if message:
            if isinstance(message, list):
                message = message[-1]
            if message.id not in _printed:
                msg_repr = message.pretty_repr(html=True)
                if len(msg_repr) > max_length:
                    msg_repr = msg_repr[:max_length] + " ... (truncated)"
                print(msg_repr)
                _printed.add(message.id)

    def _show_event(self, event: dict, _printed: set, max_length=1500) -> str:
        output = []

        current_state = event.get("dialog_state")
        if current_state:
            output.append(f"Currently in: {current_state[-1]}")

        message = event.get("messages")
        if message:
            if isinstance(message, list):
                message = message[-1]
            if message.id not in _printed:
                msg_repr = message.pretty_repr(html=True)
                if len(msg_repr) > max_length:
                    msg_repr = msg_repr[:max_length] + " ... (truncated)"
                output.append(msg_repr)
                _printed.add(message.id)

        return "".join(output)

    def build_graph(self) -> CompiledStateGraph:
        # Graph
        builder = StateGraph(State)

        # Define nodes: these do the work
        builder.add_node("assistant", self.assistant)
        builder.add_node("tools", self.create_tool_node_with_fallback(self.tools))
        # Define edges: these determine how the control flow moves
        builder.add_edge(START, "assistant")
        builder.add_conditional_edges(
            "assistant",
            tools_condition,
        )
        builder.add_edge("tools", "assistant")

        # The checkpointer lets the graph persist its state
        # this is a complete memory for the entire graph.
        return builder.compile(checkpointer=self.memory)

    def debug_chat(self):
        while True:
            user_input = input("You: ")
            events = self.build_graph().stream({"messages": ("user", f"{user_input}")}, self.config,
                                               stream_mode="values")
            if user_input.lower() == "exit":
                print("Goodbye!")
                break
            else:
                for event in events:
                    self._print_event(event, self._printed)

    def chat(self, user_input):
        events = self.build_graph().stream({"messages": ("user", f"{user_input}")}, self.config,
                                           stream_mode="values")
        output = ""
        for event in events:
            output += str(self._show_event(event, self._printed))
        return output
