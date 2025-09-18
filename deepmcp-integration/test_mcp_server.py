#!/usr/bin/env python3
"""
Simple MCP Test Server for DeepMCPAgent Integration
"""
import asyncio
import json
from mcp.server import Server
from mcp.server.models import InitializationOptions
from mcp.types import Tool, TextContent
import mcp.server.stdio

# Create server instance
server = Server("test-mcp-server")

@server.list_tools()
async def handle_list_tools() -> list[Tool]:
    """List available tools."""
    return [
        Tool(
            name="get_current_time",
            description="Get the current date and time",
            inputSchema={
                "type": "object",
                "properties": {
                    "timezone": {
                        "type": "string",
                        "description": "Timezone (default: UTC)"
                    }
                }
            }
        ),
        Tool(
            name="fetch_url",
            description="Fetch content from a URL",
            inputSchema={
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string",
                        "description": "The URL to fetch"
                    },
                    "method": {
                        "type": "string",
                        "description": "HTTP method (GET, POST, etc.)",
                        "default": "GET"
                    }
                },
                "required": ["url"]
            }
        )
    ]

@server.call_tool()
async def handle_call_tool(name: str, arguments: dict) -> list[TextContent]:
    """Handle tool calls."""
    if name == "get_current_time":
        import datetime
        timezone = arguments.get("timezone", "UTC")
        now = datetime.datetime.now()
        return [TextContent(
            type="text",
            text=f"Current time: {now.strftime('%Y-%m-%d %H:%M:%S')} ({timezone})"
        )]

    elif name == "fetch_url":
        import aiohttp
        url = arguments["url"]
        method = arguments.get("method", "GET")

        try:
            async with aiohttp.ClientSession() as session:
                async with session.request(method, url) as response:
                    content = await response.text()
                    return [TextContent(
                        type="text",
                        text=f"Status: {response.status}\nContent: {content[:500]}"
                    )]
        except Exception as e:
            return [TextContent(
                type="text",
                text=f"Error fetching {url}: {str(e)}"
            )]

    else:
        raise ValueError(f"Unknown tool: {name}")

async def main():
    # Run the server using stdio transport
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="test-mcp-server",
                server_version="1.0.0",
                capabilities=server.get_capabilities(
                    notification_options=None,
                    experimental_capabilities=None,
                ),
            ),
        )

if __name__ == "__main__":
    asyncio.run(main())