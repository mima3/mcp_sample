import asyncio
from dotenv import load_dotenv
from pathlib import Path

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

async def main() -> None:
    path = Path("./simple_stdio_server.py").resolve()
    options = ClaudeAgentOptions(
        mcp_servers={
            "calculate": {
                "type": "stdio",
                "command": "uv",
                "args": [
                    "--directory",
                    str(path.parent),
                    "run",
                    "python",
                    "simple_stdio_server.py"
                ]
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