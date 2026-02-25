import asyncio
from pathlib import Path
from dotenv import load_dotenv
from agents import Agent, Runner, ModelSettings
from agents.mcp import MCPServerStdio


load_dotenv()  # load environment variables from .env

MODEL_NAME = "gpt-5-nano"

async def main() -> None:
    path = Path("./simple_stdio_server.py").resolve()
    async with MCPServerStdio(
        name="calculate",
        params = {
            "command": "uv",
            "args": [
                "--directory",
                str(path.parent),
                "run",
                "python",
                "simple_stdio_server.py"
            ]
        }
    ) as server:
        agent = Agent(
            name="sample-agent",
            model="gpt-5-nano",
            model_settings=ModelSettings(tool_choice="required"),
            mcp_servers=[server],
            instructions="mcp serverを使用して次に与える合計を計算してください。また使用したmcp serverのツール名も出力してください。",
        )
        result = await Runner.run(agent, input="2,4,6")
        print(result.final_output) 

if __name__ == "__main__":
    asyncio.run(main())
