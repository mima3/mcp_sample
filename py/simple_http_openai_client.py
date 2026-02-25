# https://github.com/modelcontextprotocol/quickstart-resources/blob/main/mcp-client-python/client.py
# https://github.com/M6saw0/mcp-client-sample/blob/main/for-llm/tool_schemas.py
import asyncio
import json
from openai import OpenAI
from dotenv import load_dotenv
from mcp import ClientSession
from mcp.types import Tool
from mcp.client.streamable_http import streamable_http_client
from typing import Any, Dict, cast
from openai.types.responses.response_input_param import ResponseInputItemParam


load_dotenv()  # load environment variables from .env

STREAMABLE_HTTP_URL = "http://127.0.0.1:8000/mcp"
open_ai = OpenAI()
MODEL_NAME = "gpt-5-nano"

def make_tool(tool: Tool) -> Dict[str, Any]:
    parameters = tool.inputSchema.copy()
    if "type" not in parameters:
        parameters["type"] = "object"
    parameters["additionalProperties"] = False
    return {
        "type": "function",
        "name": tool.name,
        "description": tool.description,
        "parameters": parameters,
        "strict": True
    }


async def main() -> None:
    async with streamable_http_client(STREAMABLE_HTTP_URL) as (read, write, get_session_id):
        async with ClientSession(
            read,
            write,
        ) as session:
            await session.initialize()

            if (session_id := get_session_id()) is not None:
                print("Session ID:", session_id)
            print("---")

            response = await session.list_tools()
            # print("Available tools raw:", tools)
            available_tools = [make_tool(tool) for tool in response.tools]
            print("Available tools:", available_tools)
            print("---")

            # Initial Claude API call
            input_items = cast(
                list[ResponseInputItemParam],
                [
                    {
                        "role": "user", "content": "mcp serverを使用して1,2,3の合計を取得してください"
                    }
                ]
            )
            tools_param = cast(list[Any], [make_tool(tool) for tool in response.tools])
            response = open_ai.responses.create(
                model=MODEL_NAME,
                max_output_tokens=1000,
                tool_choice="required",
                input=input_items,
                tools=tools_param
            )
            print(response)
            for output in response.output:
                print('output', output)
                if output.type == "message":
                    print("  text:", output.content)
                elif output.type == "function_call":
                    args = json.loads(output.arguments or "{}")
                    print("  tool", args, output.name)
                    tool_result = await session.call_tool(output.name, args)
                    print('  tool result:', tool_result)
                    
                    response = open_ai.responses.create(
                        model=MODEL_NAME,
                        max_output_tokens=1000,
                        input=[
                            {
                                "role": "user",
                                "content": f"mcp serverの結果が次の通りになりました。日本語で結果を答えてください。\n{tool_result.content}"
                            }
                        ],
                    )
                    print('   tools after chat:', response.output_text)


if __name__ == "__main__":
    asyncio.run(main())
