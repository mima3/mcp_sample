"""FastMCP StreamableHTTP client that exercises the demo server."""

from __future__ import annotations

import asyncio
from pathlib import Path
from pydantic import FileUrl
from contextlib import asynccontextmanager
from typing import AsyncIterator, Callable, cast
from openai import OpenAI
from openai.types.responses.response_input_param import ResponseInputItemParam
from openai.types.responses.response_input_message_content_list_param import ResponseInputTextParam
from mcp.client.session import ClientSession
from mcp.client.streamable_http import streamable_http_client
from mcp import types  # ← mcp.types をまとめて参照
from dotenv import load_dotenv
from mcp.shared.context import RequestContext


STREAMABLE_HTTP_URL = "http://127.0.0.1:8000/mcp"


load_dotenv()  # load environment variables from .env

OPEN_AI_MODEL = "gpt-5-nano"
open_ai = OpenAI()

# -----------------------------
# Roots (server -> client: roots/list)
# -----------------------------
async def list_roots_callback(
    context: RequestContext[ClientSession, object, object],
) -> types.ListRootsResult:
    print('list_roots_callback called with context:', context)
    path = Path("./").resolve()
    roots = [
        types.Root(
            uri=FileUrl(str(path)),
            name="project",
        )
    ]
    return types.ListRootsResult(roots=roots)

async def handle_sampling(context: RequestContext[ClientSession, None], params: types.CreateMessageRequestParams):
    """
    サーバーから来た SamplingRequest を
    OpenAI API に渡す。
    """
    print("handle_sampling called with request:", params.messages, params.maxTokens)
    input_items: list[ResponseInputItemParam] = []
    for message in params.messages:
        text = message.content.text if isinstance(message.content, types.TextContent) else ""
        content: list[ResponseInputTextParam] = [
            {
                "type": "input_text",
                "text": text,
            }
        ]
        role = 'system'
        if message.role in ["user", "system", "developer"]:
            role = message.role
        input_item = cast(ResponseInputItemParam, {"role": role, "content": content})
        input_items.append(input_item)

    response = open_ai.responses.create(
        model=OPEN_AI_MODEL,
        input=input_items,
        max_output_tokens=params.maxTokens,
    )
    print("  OpenAI response:", response)
    return types.CreateMessageResult(
        role="assistant",
        content=types.TextContent(
            type="text",
            text=response.output_text,
        ),
        model=OPEN_AI_MODEL,
        stopReason="endTurn",
    )

async def handle_elicitation(context: RequestContext[ClientSession, None], params: types.ElicitRequestParams):
    print("handle_elicitation", params)
    print("入力してください:")
    answer = input("続行しますか?(y/n):")
    if answer == "n":
        return types.ElicitResult(
            action="cancel",
        )
    else:
        return types.ElicitResult(
            action="accept",
            content= {
                "checkAnswer": True
            }
        )

@asynccontextmanager
async def connect_to_demo(url: str) -> AsyncIterator[tuple[ClientSession, Callable[[], str | None]]]:
    async with streamable_http_client(url) as (read, write, get_session_id):
        async with ClientSession(
            read,
            write,
            list_roots_callback=list_roots_callback,
            sampling_callback=handle_sampling,
            elicitation_callback=handle_elicitation
        ) as session:
            await session.initialize()
            yield session, get_session_id


async def main() -> None:
    async with connect_to_demo(STREAMABLE_HTTP_URL) as (session, get_session_id):        
        add_result = await session.call_tool("calculator_sum", arguments={"numbers": [2, 5]})
        print("calculator_sum result:", add_result.content, add_result.isError)
        print("---")


if __name__ == "__main__":
    asyncio.run(main())
