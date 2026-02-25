import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import { z } from "zod";

const server = new McpServer({
  name: "Calculator MCP Server",
  version: "1.0.0",
});

server.registerTool(
  "sum",
  {
    title: "数値を合計する",
    description: "指定されたすべての数値の合計を計算する ",
    inputSchema: {
      numbers: z.array(z.number()).describe("数値の配列"),
    }
  },
  async ({ numbers }) => {
    const sum = numbers.reduce((acc, num) => acc + num, 0);
    return {
      content: [{ type: "text", text: String(sum) }],
    };
  }
);

// Start the server
async function main() {
  const transport = new StdioServerTransport();
  await server.connect(transport);
  console.error("Calculator MCP Server running on stdio");
}

main().catch((error) => {
  console.error("Fatal error in main():", error);
  process.exit(1);
});
