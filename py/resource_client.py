import asyncio
from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client
from mcp import types


STREAMABLE_HTTP_URL = "http://127.0.0.1:8000/mcp"

async def main() -> None:
    async with streamable_http_client(STREAMABLE_HTTP_URL) as (read, write, get_session_id):
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

            # Resourceの一覧を取得
            resources = await session.list_resources()
            print("Resource URIs:", [resource.uri for resource in resources.resources])
            print("---")
            for resource in resources.resources:
                resource_content = await session.read_resource(resource.uri)
                print(f"{resource.uri}:", resource_content.contents)
            print("---")

            # Resource Templateの一覧を取得
            templates = await session.list_resource_templates()
            print(
                "Resource templates:",
                [
                    template
                    for template in templates.resourceTemplates
                ],
            )
            print("---")
            templateUri = templates.resourceTemplates[0].uriTemplate.format(index=0)
            resource_content = await session.read_resource(types.AnyUrl(templateUri))
            print(f"{templateUri}:", resource_content.contents)
            print("---")

            prompts = await session.list_prompts()
            print("Available prompts:", [prompt.name for prompt in prompts.prompts])
            print("---")
            prompt_inputs = [
                ("calc_with_history", {"numbers": "[1,2,3]"}),
            ]
            for name, arguments in prompt_inputs:
                prompt_result = await session.get_prompt(name, arguments=arguments)
                print(f"{name} prompt:", prompt_result.messages)
            print("---")

if __name__ == "__main__":
    asyncio.run(main())
