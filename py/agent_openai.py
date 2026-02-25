from agents import Agent, Runner, function_tool, ModelSettings
import dotenv

dotenv.load_dotenv()

@function_tool
def calculator_sum(numbers: list[float]) -> float:
    """与えられた数値のリストの合計を計算するツール。

    Args:
        numbers: 合計する数値のリスト
    """
    print('call calculator_sum*****', numbers)
    return sum(numbers)

agent = Agent(
    name="calculator-agent",
    instructions="You are a calculator. Use the appropriate tool.",
    tools=[calculator_sum],
    model="gpt-5-nano",
    model_settings=ModelSettings(
        tool_choice="required"
    )
)

result = Runner.run_sync(
    agent,
    input="1,2,3の合計は？"
)

# 出力
print(result.final_output)   # JS: result.finalOutput
