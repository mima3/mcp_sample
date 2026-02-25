# https://github.com/modelcontextprotocol/quickstart-resources/blob/main/mcp-client-python/client.py
# https://github.com/M6saw0/mcp-client-sample/blob/main/for-llm/tool_schemas.py
import asyncio
import os
import httpx
from agents import Agent, Runner, ModelSettings
from agents.mcp import MCPServerStreamableHttp
from dotenv import load_dotenv


load_dotenv()  # load environment variables from .env

STREAMABLE_HTTP_URL = "http://127.0.0.1:8000/mcp"
MODEL_NAME = "gpt-5-nano"
OAUTH_CLIENT_ID = os.getenv("OAUTH_CLIENT_ID")
OAUTH_CLIENT_SECRET = os.getenv("OAUTH_CLIENT_SECRET")
KEYCLOAK_BASE = "http://localhost:8080"
REALM = "master"
WELL_KNOWN_ENDPOINT = f"{KEYCLOAK_BASE}/realms/{REALM}/.well-known/openid-configuration"

async def get_access_token() -> str:
    async with httpx.AsyncClient(timeout=10) as client:
        r = await client.get(WELL_KNOWN_ENDPOINT)
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
        print("get_access_token", token_url, r.status_code)
        r.raise_for_status()
        return r.json()["access_token"]
    

async def main() -> None:
    token = await get_access_token()

    async with MCPServerStreamableHttp(
        name="calculate",
        params = {
            "url": STREAMABLE_HTTP_URL,
            "headers": {"Authorization": f"Bearer {token}"},
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
