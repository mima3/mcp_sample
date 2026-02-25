from mcp.server.fastmcp import FastMCP
from pydantic import BaseModel

# FastMCPサーバーの初期化
mcp = FastMCP("CalculatorMCPServer")

class CalculatorResult(BaseModel):
    input: list[float]
    total: float

@mcp.tool()
async def calculator_sum(numbers: list[float]) -> CalculatorResult:
    """与えられた数値のリストの合計を計算するツール。

    Args:
        numbers: 合計を計算する数値のリスト。
    """
    total = sum(numbers)
    return CalculatorResult(
        input = numbers,
        total = total
    )

def main():
    # サーバーを初期化して実行
    mcp.run(transport="stdio")

if __name__ == "__main__":
    main()
