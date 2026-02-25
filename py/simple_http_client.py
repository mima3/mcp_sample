# https://github.com/modelcontextprotocol/quickstart-resources/blob/main/mcp-client-python/client.py
import asyncio
from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client


STREAMABLE_HTTP_URL = "http://127.0.0.1:8000/mcp"

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
            print("Available tools raw:", response.tools)
            print("---")

            result = await session.call_tool("calculator_sum", {
                "numbers": [1,2,3]
            })
            print("  tools:", result)

if __name__ == "__main__":
    asyncio.run(main())
