#!/usr/bin/env python3
"""
MCP Integration Hub: Universal MCP Server Bridge
Provides multiple integration pathways for MCP servers across your AI stack:
1. Chat Copilot + DeepMCPAgent (hybrid approach)
2. OpenWebUI integration via function calling
3. vLLM router integration via OpenAI function schema

This hub runs multiple MCP servers and exposes them via different interfaces.
"""

import asyncio
import json
import subprocess
import signal
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from pydantic import BaseModel
import logging
import uuid

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class MCPServerConfig:
    name: str
    command: List[str]
    port: int
    process: Optional[subprocess.Popen] = None
    working_dir: Optional[str] = None
    initialized: bool = False

class ToolCall(BaseModel):
    name: str
    arguments: Dict[str, Any]

class MCPResponse(BaseModel):
    success: bool
    result: Optional[Any] = None
    error: Optional[str] = None

class OpenWebUIIntegration:
    def __init__(self, mcp_hub):
        self.mcp_hub = mcp_hub

    def get_openwebui_functions(self) -> List[Dict[str, Any]]:
        """Convert MCP tools to OpenWebUI function format"""
        functions = [
            {
                "type": "function",
                "function": {
                    "name": "read_file",
                    "description": "Read contents of a file",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "path": {"type": "string", "description": "File path to read"}
                        },
                        "required": ["path"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "create_entity",
                    "description": "Create a new entity in the knowledge graph",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "name": {"type": "string", "description": "Entity name"},
                            "entity_type": {"type": "string", "description": "Type of entity"},
                            "observations": {"type": "array", "items": {"type": "string"}, "description": "List of observations about the entity"}
                        },
                        "required": ["name", "entity_type"]
                    }
                }
            }
        ]
        return functions

class VLLMIntegration:
    def __init__(self, mcp_hub):
        self.mcp_hub = mcp_hub

    def get_vllm_tools(self) -> List[Dict[str, Any]]:
        """Convert MCP tools to vLLM/OpenAI function calling format"""
        tools = [
            {
                "type": "function",
                "function": {
                    "name": "read_file",
                    "description": "Read contents of a file from the filesystem",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "path": {"type": "string", "description": "Full path to the file to read"}
                        },
                        "required": ["path"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "create_entity",
                    "description": "Create a new entity in the knowledge graph with observations",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "name": {"type": "string", "description": "Name of the entity to create"},
                            "entity_type": {"type": "string", "description": "Type/category of the entity"},
                            "observations": {"type": "array", "items": {"type": "string"}, "description": "List of observations about this entity"}
                        },
                        "required": ["name", "entity_type"]
                    }
                }
            }
        ]
        return tools

class MCPIntegrationHub:
    def __init__(self):
        self.servers: Dict[str, MCPServerConfig] = {}
        self.app = FastAPI(title="MCP Integration Hub", version="1.0.0")
        self.setup_cors()
        self.setup_routes()

        # Integration components
        self.openwebui = OpenWebUIIntegration(self)
        self.vllm = VLLMIntegration(self)

    def setup_cors(self):
        """Setup CORS for cross-origin requests from OpenWebUI"""
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    def setup_routes(self):
        """Setup FastAPI routes for different integration types"""

        @self.app.get("/")
        async def root():
            return {
                "service": "MCP Integration Hub",
                "version": "1.0.0",
                "integrations": ["chat-copilot", "openwebui", "vllm"],
                "active_servers": list(self.servers.keys())
            }

        @self.app.get("/openwebui/functions")
        async def get_openwebui_functions():
            """OpenWebUI function definitions endpoint"""
            return self.openwebui.get_openwebui_functions()

        @self.app.post("/openwebui/execute")
        async def execute_openwebui_function(tool_call: ToolCall):
            """Execute function called from OpenWebUI"""
            try:
                result = await self.execute_mcp_tool(tool_call.name, tool_call.arguments)
                return MCPResponse(success=True, result=result)
            except Exception as e:
                return MCPResponse(success=False, error=str(e))

        @self.app.get("/vllm/tools")
        async def get_vllm_tools():
            """vLLM router compatible tool definitions"""
            return self.vllm.get_vllm_tools()

        @self.app.post("/vllm/execute")
        async def execute_vllm_function(tool_call: ToolCall):
            """Execute function called from vLLM router"""
            try:
                result = await self.execute_mcp_tool(tool_call.name, tool_call.arguments)
                return MCPResponse(success=True, result=result)
            except Exception as e:
                return MCPResponse(success=False, error=str(e))

        @self.app.get("/health")
        async def health_check():
            return {"status": "healthy", "timestamp": datetime.now().isoformat()}

    async def call_mcp_server(self, server_name: str, method: str, params: Any = None) -> Any:
        """Call an MCP server using JSON-RPC protocol"""
        if server_name not in self.servers:
            raise ValueError(f"Server {server_name} not configured")

        config = self.servers[server_name]
        if not config.process or config.process.poll() is not None:
            raise RuntimeError(f"Server {server_name} is not running")

        # Create JSON-RPC request
        request_id = str(uuid.uuid4())
        request = {
            "jsonrpc": "2.0",
            "id": request_id,
            "method": method,
            "params": params or {}
        }

        try:
            # Send request to MCP server
            request_json = json.dumps(request) + "\n"
            config.process.stdin.write(request_json)
            config.process.stdin.flush()

            # Read response (with timeout)
            response_line = await asyncio.wait_for(
                asyncio.to_thread(config.process.stdout.readline),
                timeout=10.0
            )

            if not response_line:
                raise RuntimeError(f"No response from {server_name}")

            response = json.loads(response_line.strip())

            if "error" in response:
                raise RuntimeError(f"MCP Error: {response['error']}")

            return response.get("result")

        except Exception as e:
            logger.error(f"Failed to communicate with {server_name}: {e}")
            raise

    async def initialize_mcp_servers(self):
        """Initialize MCP servers with handshake if not already done"""
        for server_name, config in self.servers.items():
            if not config.initialized:
                try:
                    # Send initialize request
                    init_result = await self.call_mcp_server(server_name, "initialize", {
                        "protocolVersion": "2024-11-05",
                        "capabilities": {"tools": {}},
                        "clientInfo": {"name": "mcp-integration-hub", "version": "1.0.0"}
                    })
                    config.initialized = True
                    logger.info(f"✅ Initialized MCP server: {server_name}")
                except Exception as e:
                    logger.warning(f"Failed to initialize {server_name}: {e}")

    async def execute_mcp_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Any:
        """Execute an MCP tool by routing to appropriate server"""

        try:
            # Initialize MCP session if not done already
            await self.initialize_mcp_servers()

            # Route tool calls to appropriate MCP servers
            if tool_name in ["read_file", "write_file", "list_directory"]:
                # Filesystem operations
                result = await self.call_mcp_server("filesystem", "tools/call", {
                    "name": tool_name,
                    "arguments": arguments
                })
                return result

            elif tool_name in ["create_entity", "query_memory", "search_entities"]:
                # Memory/knowledge graph operations
                result = await self.call_mcp_server("memory", "tools/call", {
                    "name": tool_name,
                    "arguments": arguments
                })
                return result

            elif tool_name in ["get_current_time", "git_log"]:
                # General utilities and everything server
                result = await self.call_mcp_server("everything", "tools/call", {
                    "name": tool_name,
                    "arguments": arguments
                })
                return result

            elif tool_name in ["thinking_step", "analyze_problem"]:
                # Sequential thinking operations
                result = await self.call_mcp_server("sequentialthinking", "tools/call", {
                    "name": tool_name,
                    "arguments": arguments
                })
                return result

        except Exception as e:
            logger.error(f"MCP call failed for {tool_name}: {e}")
            raise RuntimeError(f"Failed to execute {tool_name} via MCP server: {e}")

        # If we reach here, the tool is not supported
        raise ValueError(f"Tool {tool_name} not supported by any configured MCP server")

    def configure_mcp_servers(self):
        """Configure the MCP servers to start"""

        # Real MCP servers path
        mcp_base = Path("/home/keith/servers/src")

        self.servers = {
            "memory": MCPServerConfig(
                name="memory",
                command=["node", str(mcp_base / "memory" / "dist" / "index.js")],
                port=11015,
                working_dir=str(mcp_base / "memory")
            ),
            "filesystem": MCPServerConfig(
                name="filesystem",
                command=["node", str(mcp_base / "filesystem" / "dist" / "index.js"), "/tmp"],
                port=11014,
                working_dir=str(mcp_base / "filesystem")
            ),
            "everything": MCPServerConfig(
                name="everything",
                command=["node", str(mcp_base / "everything" / "dist" / "index.js")],
                port=11013,
                working_dir=str(mcp_base / "everything")
            ),
            "sequentialthinking": MCPServerConfig(
                name="sequentialthinking",
                command=["node", str(mcp_base / "sequentialthinking" / "dist" / "index.js")],
                port=11012,
                working_dir=str(mcp_base / "sequentialthinking")
            )
        }

    async def start_mcp_servers(self):
        """Start all configured MCP servers"""
        logger.info("Starting MCP servers...")

        for name, config in self.servers.items():
            try:
                logger.info(f"Starting {name} server...")

                # Start the actual MCP server process
                config.process = subprocess.Popen(
                    config.command,
                    stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    cwd=config.working_dir,
                    text=True,
                    bufsize=1,
                    universal_newlines=True
                )

                # Give the process a moment to start
                await asyncio.sleep(0.5)

                # Check if the process is still running
                if config.process.poll() is None:
                    logger.info(f"✅ {name} server started successfully (PID: {config.process.pid})")
                else:
                    # Process died immediately, read stderr for error
                    stderr_output = config.process.stderr.read()
                    logger.error(f"❌ {name} server failed to start: {stderr_output}")

            except Exception as e:
                logger.error(f"Failed to start {name} server: {e}")

    def stop_mcp_servers(self):
        """Stop all MCP servers"""
        logger.info("Stopping MCP servers...")
        for name, config in self.servers.items():
            if config.process:
                config.process.terminate()
                logger.info(f"Stopped {name} server")

    async def run_server(self, host="0.0.0.0", port=11010):
        """Run the integration hub server"""
        self.configure_mcp_servers()
        await self.start_mcp_servers()

        logger.info(f"🚀 MCP Integration Hub starting on http://{host}:{port}")
        logger.info("📡 Available integrations:")
        logger.info("   • Chat Copilot + DeepMCPAgent: http://localhost:11010/deepmcp/")
        logger.info("   • OpenWebUI Functions: http://localhost:11010/openwebui/")
        logger.info("   • vLLM Router Tools: http://localhost:11010/vllm/")

        # Handle shutdown gracefully
        def signal_handler(signum, frame):
            logger.info("Shutting down...")
            self.stop_mcp_servers()
            sys.exit(0)

        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

        # Run the server
        config = uvicorn.Config(self.app, host=host, port=port, log_level="info")
        server = uvicorn.Server(config)
        await server.serve()

if __name__ == "__main__":
    hub = MCPIntegrationHub()
    asyncio.run(hub.run_server())