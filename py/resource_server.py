from mcp.server.fastmcp import FastMCP, Context
from mcp.server.fastmcp.utilities.logging import get_logger
from pydantic import BaseModel
logger = get_logger("FastMCP.Server")
mcp = FastMCP("CalculatorMCPServer", host="127.0.0.1", port=8000)
calculation_history = []

class CalculatorResult(BaseModel):
    input: list[float]
    total: float

@mcp.resource("calculator://history")
async def get_history() -> str:
    """これまでの計算履歴を返す。"""
    logger.info('get_history called')
    if not calculation_history:
        return "No calculations yet."
    return "\n".join(calculation_history)

@mcp.resource("calculator://history/{index}")
async def get_history_item(index: int) -> str:
    """履歴の特定インデックスを返す。"""
    logger.info('get_history_item called with index: %d', index)
    if not calculation_history:
        return "No calculations yet."

    if index < 0 or index >= len(calculation_history):
        return f"Index {index} is out of range."

    return calculation_history[index]

@mcp.prompt()
async def calc_with_history(numbers: str) -> str:
    """
    このサーバーの tool と resource をどう使うかをガイドするプロンプト
    """
    return f"""
あなたは電卓アシスタントです。

まず、このMCPサーバーの tool `calculator_sum` を使って次を計算してください:
- numbers = {numbers}

計算後、このMCPサーバーの resource `calculator://history` を参照し、
今回の計算が履歴に追加されていることを確認して、最後に要約してください。
"""

@mcp.tool()
async def calculator_sum(numbers: list[float], ctx: Context) -> CalculatorResult:
    """与えられた数値のリストの合計を計算するツール。

    Args:
        numbers: 合計を計算する数値のリスト。
    """
    logger.info(f"calculator_sum called with numbers: {numbers} ")
    total = sum(numbers)
    logger.info(f"calculator_sum result {total} ")
    calculation_history.append(f"{numbers} is {total}")
    return CalculatorResult(
        input = numbers,
        total = total
    )


def main():
    logger.info('start main...')
    # FastMCP docs: transport="http" + host/port
    # Server endpoint will be: http://127.0.0.1:8000/mcp
    mcp.run(transport="streamable-http")

if __name__ == "__main__":
    main()
