# https://github.com/modelcontextprotocol/quickstart-resources/blob/main/mcp-client-python/client.py
# https://github.com/M6saw0/mcp-client-sample/blob/main/for-llm/tool_schemas.py
import asyncio
import json
import os
import httpx
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
OAUTH_CLIENT_ID = os.getenv("OAUTH_CLIENT_ID")
OAUTH_CLIENT_SECRET = os.getenv("OAUTH_CLIENT_SECRET")
KEYCLOAK_BASE = "http://localhost:8080"
REALM = "master"
WELL_KNOWN_ENDPOINT = f"{KEYCLOAK_BASE}/realms/{REALM}/.well-known/openid-configuration"

async def get_access_token() -> str:
    async with httpx.AsyncClient(timeout=10) as client:
        r = await client.get(WELL_KNOWN_ENDPOINT)
        print(r)
        r.raise_for_status()
        token_url = r.json()['token_endpoint']
        r = await client.post(
            token_url,
            data={
                "grant_type": "client_credentials",
                "client_id": OAUTH_CLIENT_ID,
                "client_secret": OAUTH_CLIENT_SECRET,
                "scope": "mcp:tools"
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        print(r.status_code)
        print(r.text) 
        print("get_access_token", token_url, r)
        r.raise_for_status()
        return r.json()["access_token"]
    
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
    token = await get_access_token()

    # Bearer token を付けた httpx client を streamable_http_client に渡す
    async with httpx.AsyncClient(
        headers={"Authorization": f"Bearer {token}"},
        timeout=30,
        follow_redirects=True,
    ) as http_client:
        async with streamable_http_client(STREAMABLE_HTTP_URL, http_client=http_client) as (read, write, get_session_id):
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
