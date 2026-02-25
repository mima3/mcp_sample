# https://github.com/modelcontextprotocol/quickstart-resources/blob/main/mcp-client-python/client.py
import asyncio
import os
from anthropic import Anthropic
from anthropic.types.tool_union_param import ToolUnionParam
from typing import cast, Iterable
from dotenv import load_dotenv
from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client


load_dotenv()  # load environment variables from .env

STREAMABLE_HTTP_URL = "http://127.0.0.1:8000/mcp"
anthropic = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
MODEL_NAME = "claude-haiku-4-5-20251001"

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
            print("Available tools:", [tool.name for tool in response.tools])
            print("---")

            available_tools: Iterable[ToolUnionParam] = cast(
                Iterable[ToolUnionParam],
                [
                    {
                        "name": tool.name,
                        "description": tool.description,
                        "input_schema": tool.inputSchema
                    }
                    for tool in response.tools
                ]
            )

            # Initial Claude API call
            response = anthropic.messages.create(
                model=MODEL_NAME,
                max_tokens=1000,
                messages=[
                    {
                        "role": "user", "content": "mcp serverを使用して1,2,3の合計を取得してください"
                    }
                ],
                tools=available_tools
            )
            print(response)
            for content in response.content:
                print('content', content)
                if content.type == "text":
                    print("  text:", content.text)
                elif content.type == "tool_use":
                    tool_name = content.name
                    tool_args = content.input

                    # Execute tool call
                    result = await session.call_tool(tool_name, tool_args)
                    print("  tools:", result)
                    response = anthropic.messages.create(
                        model=MODEL_NAME,
                        max_tokens=1000,
                        messages=[
                            {
                                "role": "user",
                                "content": f"mcp serverの結果が次の通りになりました。日本語で結果を答えてください。\n{result.content}"
                            }
                        ],
                    )
                    print('   tools after chat:', response.content)


if __name__ == "__main__":
    asyncio.run(main())
