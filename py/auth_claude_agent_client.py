import asyncio
import os
import httpx
from dotenv import load_dotenv

from claude_agent_sdk import (
    query,
    ClaudeAgentOptions,
    AssistantMessage,
    SystemMessage,
    ResultMessage,
    ToolUseBlock,
    TextBlock,
)

load_dotenv()

STREAMABLE_HTTP_URL = "http://127.0.0.1:8000/mcp"

OAUTH_CLIENT_ID = os.getenv("OAUTH_CLIENT_ID")
OAUTH_CLIENT_SECRET = os.getenv("OAUTH_CLIENT_SECRET")
KEYCLOAK_BASE = "http://localhost:8080"
REALM = "master"
WELL_KNOWN_ENDPOINT = f"{KEYCLOAK_BASE}/realms/{REALM}/.well-known/openid-configuration"

REQUIRED_SCOPE = "mcp:tools"


async def get_access_token() -> str:
    async with httpx.AsyncClient(timeout=10) as client:
        r = await client.get(WELL_KNOWN_ENDPOINT)
        r.raise_for_status()
        token_url = r.json()["token_endpoint"]

        r = await client.post(
            token_url,
            data={
                "grant_type": "client_credentials",
                "client_id": OAUTH_CLIENT_ID,
                "client_secret": OAUTH_CLIENT_SECRET,
                "scope": REQUIRED_SCOPE,
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        print("get_access_token", token_url, r.status_code)
        r.raise_for_status()
        return r.json()["access_token"]


async def main() -> None:
    token = await get_access_token()

    # Claude Agent SDK 側の MCP 設定（HTTP + headers）
    # - mcp_servers: dict[str, McpServerConfig]
    # - HTTP の場合: {"type": "http", "url": "...", "headers": {...}} が使える
    options = ClaudeAgentOptions(
        mcp_servers={
            "calculate": {
                "type": "http",
                "url": STREAMABLE_HTTP_URL,
                "headers": {"Authorization": f"Bearer {token}"},
            }
        },
        # MCPツールは明示許可が必要
        # 命名規約: mcp__<server-name>__<tool-name>
        # まとめて許可するならワイルドカード
        allowed_tools=["mcp__calculate__*"],
        max_turns=4,
        system_prompt=(
            "mcp serverを使用して次に与える合計を計算してください。"
            "また使用したmcp serverのツール名も出力してください。"
        ),
    )

    used_mcp_tools: list[str] = []
    final_text_parts: list[str] = []

    # query() はストリームでメッセージが流れてくる
    async for message in query(prompt="2,4,6", options=options):
        print("  ", message)
        if isinstance(message, AssistantMessage):
            for block in message.content:
                # MCPツール呼び出しを捕捉（実際に呼ばれたツール名をログ）
                if isinstance(block, ToolUseBlock) and block.name.startswith("mcp__"):
                    used_mcp_tools.append(block.name)
                # 返答テキストを収集
                if isinstance(block, TextBlock):
                    final_text_parts.append(block.text)
        elif isinstance(message, SystemMessage):
            pass
        elif isinstance(message, ResultMessage):
            pass

    print("used_mcp_tools:", used_mcp_tools)
    print("final_output:\n", "".join(final_text_parts))


if __name__ == "__main__":
    asyncio.run(main())