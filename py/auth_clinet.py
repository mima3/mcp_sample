import asyncio
import os
import httpx
from dotenv import load_dotenv
from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client


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
        r.raise_for_status()
        return r.json()["access_token"]
    
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
                print("Available tools raw:", response.tools)
                print("---")

                result = await session.call_tool("calculator_sum", {
                    "numbers": [1,2,3]
                })
                print("  tools:", result)


if __name__ == "__main__":
    asyncio.run(main())
