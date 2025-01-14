import logging
import os
import traceback
from typing import Any

from bedrock_ai.conversers.converse_agent import ConverseAgent
from bedrock_ai.conversers.converse_tools import ConverseToolManager
from bedrock_ai.mcp_client import MCPClient
from django.conf import settings
from mcp import StdioServerParameters

"""
install :
boto3>=1.35.69
mcp
uvicorn>=0.32.0
"""

logger = logging.getLogger("bedrock_ai")


class BedrockAI:
    _INSTANCE = None
    CHAT = None

    @staticmethod
    def reset_chat():
        BedrockAI.CHAT = None

    def convertToHTML(data: Any) -> str:
        html = """
            <div style="font-family: Arial, sans-serif; max-width: 600px; margin: auto; padding: 20px; border: 1px solid #ddd; border-radius: 10px; background-color: #f9f9f9;">
                <div style="padding: 10px;">
        """

        for item in data:
            roleClass = "user" if item["role"] == "user" else "assistant"
            html += f'<div class="{roleClass}" style="margin-bottom: 20px; padding: 10px; border-radius: 10px; max-width: 80%;">'
            html += f'<p>{item["content"]}</p>'
            html += "</div>"

        html += """
                </div>
            </div>
            <style>
                .user {
                    background-color: #dcf8c6;
                    text-align: left;
                    align-self: flex-start;
                    margin-left: 0;
                    margin-right: auto;
                }
                .assistant {
                    background-color: #f1f0f0;
                    text-align: left;
                    align-self: flex-end;
                    margin-left: auto;
                    margin-right: 0;
                }
                p {
                    margin: 0;
                    padding: 0;
                }
            </style>
        """

        return html

    @staticmethod
    def get_instance() -> "BedrockAI":
        if BedrockAI._INSTANCE is None:
            BedrockAI._INSTANCE = BedrockAI()
        return BedrockAI._INSTANCE

    @staticmethod
    async def prompt(user_input: str) -> str:
        try:
            inst = BedrockAI()
            if BedrockAI.CHAT is None:
                BedrockAI.CHAT = []

            result = await inst.prompt_ai(user_input)

            return result
        except Exception as exc:
            logger.exception(exc)
            BedrockAI._INSTANCE = None
            raise

    def __init__(self) -> None:
        self.model_id = settings.BEDROCK_SETTINGS["model_id"]

        # Set up the agent and tool manager
        self.agent = ConverseAgent(self.model_id)
        # self.agent.tools =

        # Define the agent's behavior through system prompt
        self.agent.system_prompt = settings.BEDROCK_SETTINGS["system_prompt"]
        self.server_params = None

    async def prompt_ai(self, user_prompt: str) -> str:

        # Create server parameters for SQLite configuration
        self.server_params = StdioServerParameters(
            command=settings.BEDROCK_SETTINGS["mcp_server"]["command"],
            args=settings.BEDROCK_SETTINGS["mcp_server"]["args"],
            env=None,
        )

        # Initialize MCP client with server parameters
        # self.mcp_client = MCPClient(self.server_params)
        # await self.mcp_client.connect()
        async with MCPClient(self.server_params) as mcp_client:

            # Fetch available tools from the MCP client
            tools = await mcp_client.get_available_tools()

            # Register each available tool with the agent
            for tool in tools:
                self.agent.tools.register_tool(
                    name=tool.name,
                    func=mcp_client.call_tool,
                    description=tool.description,
                    input_schema={"json": tool.inputSchema},
                )
            # try:
            # Process the prompt and display the response
            BedrockAI.CHAT.append({"role": "user", "content": user_prompt})
            response = await self.agent.invoke_with_prompt(user_prompt)
            BedrockAI.CHAT.append({"role": "assistant", "content": response})
            logger.info("\nResponse:", response)

            # await self.mcp_client.session.__aexit__(None, None, None)
            return response
            # except Exception as e:
            #     print(traceback.format_exc())
            #     print(f"\nError occurred: {e}")
            # what are my forest collections ?
            # what are the fields of the collection address ?
            # what is the primary key of my collection address ?
            # what are the relations of the collection address ?
            # what are the vip customers ?
