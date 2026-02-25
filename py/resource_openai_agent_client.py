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
        res = await server.list_prompts()
        for prompt in res.prompts:
            print("prompt", prompt)
        print(res.prompts[0].name)
        res = await server.get_prompt(res.prompts[0].name, {
            "numbers": "[1,2,3]"
        })
        print(res.messages)
        agent = Agent(
            name="sample-agent",
            model="gpt-5-nano",
            model_settings=ModelSettings(tool_choice="required"),
            mcp_servers=[server],
            instructions="計算をサポートするMCP Server serverを利用して利用可能なリソースの一覧を提示してください。取得できない場合はその理由を出力してください"
        )
        result = await Runner.run(agent, input="2,4,6")
        print(result.final_output) 

if __name__ == "__main__":
    asyncio.run(main())
