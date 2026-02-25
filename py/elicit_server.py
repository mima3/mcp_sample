from mcp.server.fastmcp import FastMCP, Context
from mcp.server.fastmcp.utilities.logging import get_logger
from mcp import types
from pydantic import BaseModel, Field

logger = get_logger("FastMCP.Server")
mcp = FastMCP("CalculatorMCPServer", host="127.0.0.1", port=8000)

class ElicitData(BaseModel):
    checkAnswer: bool = Field(description="つづけていいか?")


@mcp.tool()
async def calculator_sum(numbers: list[float], ctx: Context) -> str:
    """与えられた数値のリストの合計を計算するツール。

    Args:
        numbers: 合計を計算する数値のリスト。
    """
    logger.info(f"calculator_sum called with numbers: {numbers} ")
    # elicitの事例: MCP Clientにユーザーの問い合わせをするように依頼する
    try:
        result = await ctx.elicit(
            message=(
                "calculator_sumを実行してもいいですか？.\n"
            ),
            schema=ElicitData,
        )
    except Exception as e:
        logger.error(f"Error elicit: {e}")
        return "Error elicit"
    logger.info(f"elicit result. {result}")
    if result.action != "accept":
        logger.error('キャンセルされました')
        return "Canceled"
    # rootsの事例: MCP Clientからrootsの情報を取得する
    try:
        roots = await ctx.session.list_roots()
        logger.info([r.uri for r in roots.roots])
    except Exception as e:
        logger.error(f"Error listing roots: {e}")
    # ツールの処理
    total = sum(numbers)
    text = f"The sum of {numbers} is {total}."
    logger.info(f"calculator_sum result {total} ")
    # samplingの事例： MCP ClientにLLMによる問い合わせを行うように依頼する
    try:
        sampling_requests = [
            types.SamplingMessage(
                role="assistant",
                content=types.TextContent(
                    type="text",
                    text="以下の計算結果を簡潔に日本語で回答せよ."
                ),
            ),
            types.SamplingMessage(
                role="user",
                content=types.TextContent(
                    type="text",
                    text=text
                ),
            ),
        ]
        result = await ctx.session.create_message(sampling_requests, max_tokens=1000)
        logger.info(f"calculator_sum : {result} ")
        logger.info(result.content.text)
        return result.content.text
    except Exception as e:
        logger.error(f"Error during sampling: {e}")
        return text

def main():
    logger.info('start main...')
    # FastMCP docs: transport="http" + host/port
    # Server endpoint will be: http://127.0.0.1:8000/mcp
    mcp.run(transport="streamable-http")

if __name__ == "__main__":
    main()
