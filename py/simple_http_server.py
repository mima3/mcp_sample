from mcp.server.fastmcp import FastMCP, Context
from mcp.server.fastmcp.utilities.logging import get_logger
from pydantic import BaseModel
logger = get_logger("FastMCP.Server")
mcp = FastMCP("CalculatorMCPServer", host="127.0.0.1", port=8000)

class CalculatorResult(BaseModel):
    input: list[float]
    total: float

@mcp.tool()
async def calculator_sum(numbers: list[float], ctx: Context) -> CalculatorResult:
    """与えられた数値のリストの合計を計算するツール。

    Args:
        numbers: 合計を計算する数値のリスト。
    """
    logger.info(f"calculator_sum called with numbers: {numbers} ")
    total = sum(numbers)
    logger.info(f"calculator_sum result {total} ")
    
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
