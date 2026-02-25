import asyncio
from dotenv import load_dotenv
from agents import Agent, Runner, ModelSettings
from agents.mcp import MCPServerStreamableHttp


load_dotenv()  # load environment variables from .env

STREAMABLE_HTTP_URL = "http://127.0.0.1:8000/mcp"
MODEL_NAME = "gpt-5-nano"

async def main() -> None:
    async with MCPServerStreamableHttp(
        name="calculate",
        params = {
            "url": STREAMABLE_HTTP_URL
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
