import asyncio
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

async def main() -> None:
    options = ClaudeAgentOptions(
        mcp_servers={
            "calculate": {
                "type": "http",
                "url": STREAMABLE_HTTP_URL,
            }
        },
        # MCPツールは明示許可が必要
        # 命名規約: mcp__<server-name>__<tool-name>
        # まとめて許可するならワイルドカード
        allowed_tools=["mcp__calculate__*"],
        max_turns=4,
        system_prompt=(
            "計算機能を提供するMCP Serverを使用して指定の数値を計算してください。"
            "同じMCP Serverが提供しているリソースから計算履歴を取得してください。"
            "上記の結果を出力してください。"
            "また、使用したTool, Resource名も列挙してください"
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