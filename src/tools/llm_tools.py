from typing import Optional
from pydantic import BaseModel, Field
from langchain.tools import tool
from langchain_community.tools.tavily_search import TavilySearchResults
from src.MqttHandler.MqttHandler import MqttHandler

handler = MqttHandler()

class SetCharacter(BaseModel):
    character: Optional[str] = Field(None, description="The character which will be set on the 8x8 matrix display.")

class ToggleDevice1(BaseModel):
    state: Optional[bool] = Field(None, description="True to turn on device 1, False to turn off")

class ToggleDevice2(BaseModel):
    state: Optional[bool] = Field(None, description="True to turn on device 2, False to turn off")

# class GetCurrentTemperature(BaseModel):
#     state: Optional[bool] = Field(None, description="Gives the current temperature in Celsius")

class ChatAssistantInput(BaseModel):
    input: str = Field(..., description="The user input")
    history: str = Field(..., description="The summarized content of chat")

@tool('get_current_temperature')
def get_current_temperature() -> Optional[float]:
    """
    Gives the current temperature in Celsius.
    """
    return handler.get_temperature()

@tool('set_character', args_schema=SetCharacter)
def set_character(character) -> None:
    """
    Sets the character on the 8x8 matrix display.
    """
    return handler.set_display(str(character))

@tool('toggle_device1', args_schema=ToggleDevice1)
def toggle_device1(state: bool, **kwargs) -> str:
    """
    Turn on or off a device 1.
    """
    output = "on" if handler.device1(state, **kwargs) else "off"
    return f"Device 1 is turned {output}\n"

@tool('toggle_device2', args_schema=ToggleDevice1)
def toggle_device2(state: bool, **kwargs) -> str:
    """
    Turn on or off a device 2.
    """
    output = "on" if handler.device2(state, **kwargs) else "off"
    return f"Device 2 is turned {output}\n"

@tool('chat_assistant', args_schema=ChatAssistantInput)
def chat_assistant(input: str, history: str, **kwargs) -> None:
    """
    Runs a small talk chat assistant
    """
    return None

def get_tools():
    return [chat_assistant, get_current_temperature, set_character, toggle_device1, toggle_device2, TavilySearchResults(max_results=3)]
