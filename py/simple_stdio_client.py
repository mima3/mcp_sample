# https://github.com/modelcontextprotocol/quickstart-resources/blob/main/mcp-client-python/client.py
import asyncio
from pathlib import Path
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


async def main() -> None:
    path = Path("./simple_stdio_server.py").resolve()
    server_params = StdioServerParameters(
        command="uv",
        args=["--directory", str(path.parent), "run", "python", path.name],
        env=None,
    )
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(
            read,
            write,
        ) as session:
            await session.initialize()

            response = await session.list_tools()
            print("Available tools raw:", response.tools)
            print("---")

            result = await session.call_tool("calculator_sum", {
                "numbers": [1,2,3]
            })
            print("  tools:", result)

if __name__ == "__main__":
    asyncio.run(main())
