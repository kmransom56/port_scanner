#!/usr/bin/env python3
"""
vLLM Router MCP Integration Configuration
Provides OpenAI-compatible function calling integration for vLLM router
"""

import json
import asyncio
import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import httpx

logger = logging.getLogger(__name__)

class VLLMFunctionCall(BaseModel):
    """OpenAI-compatible function call format for vLLM"""
    name: str
    arguments: str  # JSON string

class VLLMMessage(BaseModel):
    """OpenAI-compatible message format"""
    role: str
    content: Optional[str] = None
    function_call: Optional[VLLMFunctionCall] = None

class VLLMChatRequest(BaseModel):
    """vLLM chat completion request with function calling"""
    model: str
    messages: List[VLLMMessage]
    functions: Optional[List[Dict[str, Any]]] = None
    function_call: Optional[str] = None
    temperature: float = 0.7
    max_tokens: Optional[int] = None

class VLLMFunctionResult(BaseModel):
    """Function execution result"""
    name: str
    content: str

class VLLMRouterMCPBridge:
    """Bridge between vLLM router and MCP servers"""

    def __init__(self, mcp_hub_url: str = "http://localhost:11010"):
        self.mcp_hub_url = mcp_hub_url
        self.app = FastAPI(title="vLLM MCP Bridge", version="1.0.0")
        self.setup_routes()

    def setup_routes(self):
        """Setup vLLM-compatible endpoints"""

        @self.app.get("/v1/models")
        async def list_models():
            """List available models (vLLM compatibility)"""
            return {
                "object": "list",
                "data": [
                    {
                        "id": "meta-llama/Llama-3.1-8B-Instruct",
                        "object": "model",
                        "created": 1234567890,
                        "owned_by": "vllm-mcp-bridge"
                    }
                ]
            }

        @self.app.post("/v1/chat/completions")
        async def chat_completions(request: VLLMChatRequest):
            """
            OpenAI-compatible chat completions with MCP function calling
            This endpoint intercepts function calls and routes them to MCP servers
            """

            # Check if this is a function call
            last_message = request.messages[-1] if request.messages else None

            if (last_message and
                last_message.function_call and
                hasattr(last_message, 'function_call')):

                # Execute MCP function
                function_name = last_message.function_call.name
                arguments = json.loads(last_message.function_call.arguments)

                try:
                    result = await self.execute_mcp_function(function_name, arguments)

                    return {
                        "id": f"chatcmpl-mcp-{hash(str(arguments)) % 10000}",
                        "object": "chat.completion",
                        "created": 1234567890,
                        "model": request.model,
                        "choices": [{
                            "index": 0,
                            "message": {
                                "role": "function",
                                "name": function_name,
                                "content": json.dumps(result)
                            },
                            "finish_reason": "function_call"
                        }],
                        "usage": {
                            "prompt_tokens": 100,
                            "completion_tokens": 50,
                            "total_tokens": 150
                        }
                    }

                except Exception as e:
                    logger.error(f"Error executing MCP function {function_name}: {e}")
                    return {
                        "error": {
                            "message": f"Function execution failed: {str(e)}",
                            "type": "function_error",
                            "code": "mcp_error"
                        }
                    }

            # If not a function call, forward to actual vLLM server
            # In production, this would proxy to your vLLM endpoint
            return await self.forward_to_vllm(request)

        @self.app.get("/v1/mcp/functions")
        async def get_mcp_functions():
            """Get available MCP functions in OpenAI format"""
            try:
                async with httpx.AsyncClient() as client:
                    response = await client.get(f"{self.mcp_hub_url}/vllm/tools")
                    tools = response.json()

                    # Convert to OpenAI functions format
                    functions = []
                    for tool in tools:
                        if tool["type"] == "function":
                            functions.append(tool["function"])

                    return {"functions": functions}

            except Exception as e:
                logger.error(f"Error getting MCP functions: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.post("/v1/mcp/execute")
        async def execute_function(function_call: VLLMFunctionCall):
            """Execute MCP function directly"""
            try:
                arguments = json.loads(function_call.arguments)
                result = await self.execute_mcp_function(function_call.name, arguments)

                return VLLMFunctionResult(
                    name=function_call.name,
                    content=json.dumps(result)
                )

            except Exception as e:
                logger.error(f"Error executing function {function_call.name}: {e}")
                raise HTTPException(status_code=500, detail=str(e))

    async def execute_mcp_function(self, function_name: str, arguments: Dict[str, Any]) -> Any:
        """Execute MCP function via integration hub"""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.mcp_hub_url}/vllm/execute",
                json={
                    "name": function_name,
                    "arguments": arguments
                }
            )

            if response.status_code != 200:
                raise Exception(f"MCP hub error: {response.status_code}")

            result = response.json()

            if not result["success"]:
                raise Exception(result.get("error", "Unknown MCP error"))

            return result["result"]

    async def forward_to_vllm(self, request: VLLMChatRequest) -> Dict[str, Any]:
        """Forward non-function requests to actual vLLM server"""

        # In production, configure this to point to your vLLM server
        vllm_endpoint = "http://localhost:8000/v1/chat/completions"

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    vllm_endpoint,
                    json=request.dict()
                )

                if response.status_code == 200:
                    return response.json()
                else:
                    # Mock response if vLLM server not available
                    return {
                        "id": f"chatcmpl-mock-{hash(str(request.messages)) % 10000}",
                        "object": "chat.completion",
                        "created": 1234567890,
                        "model": request.model,
                        "choices": [{
                            "index": 0,
                            "message": {
                                "role": "assistant",
                                "content": "This is a mock response. Configure vLLM endpoint for actual completions."
                            },
                            "finish_reason": "stop"
                        }],
                        "usage": {
                            "prompt_tokens": 100,
                            "completion_tokens": 20,
                            "total_tokens": 120
                        }
                    }

        except Exception as e:
            logger.error(f"Error forwarding to vLLM: {e}")
            # Return mock response on error
            return {
                "id": f"chatcmpl-error-{hash(str(request.messages)) % 10000}",
                "object": "chat.completion",
                "created": 1234567890,
                "model": request.model,
                "choices": [{
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": f"Error connecting to vLLM server: {str(e)}"
                    },
                    "finish_reason": "error"
                }],
                "usage": {
                    "prompt_tokens": 50,
                    "completion_tokens": 10,
                    "total_tokens": 60
                }
            }

def generate_vllm_systemd_service():
    """Generate systemd service for vLLM MCP bridge"""

    service_content = """[Unit]
Description=vLLM MCP Bridge Service
After=network.target

[Service]
Type=simple
User=ai-platform-sync
Group=ai-platform-sync
WorkingDirectory=/home/keith/deepmcp-integration
Environment=PATH=/home/keith/deepmcp-integration/venv/bin:/usr/local/bin:/usr/bin:/bin
Environment=PYTHONPATH=/home/keith/deepmcp-integration
ExecStart=/home/keith/deepmcp-integration/venv/bin/python -m uvicorn vllm_mcp_bridge:app --host 0.0.0.0 --port 11011
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
"""

    return service_content

def generate_vllm_docker_config():
    """Generate Docker configuration for vLLM with MCP integration"""

    docker_config = {
        "version": "3.8",
        "services": {
            "vllm-mcp-bridge": {
                "build": {
                    "context": "/home/keith/deepmcp-integration",
                    "dockerfile": "Dockerfile.vllm"
                },
                "ports": ["11011:11011"],
                "environment": [
                    "MCP_HUB_URL=http://mcp-integration-hub:11010",
                    "VLLM_ENDPOINT=http://vllm-server:8000"
                ],
                "depends_on": ["mcp-integration-hub"],
                "networks": ["ai-platform"],
                "restart": "unless-stopped"
            },
            "vllm-server": {
                "image": "vllm/vllm-openai:latest",
                "ports": ["11002:8000"],
                "command": [
                    "--model", "meta-llama/Llama-3.1-8B-Instruct",
                    "--served-model-name", "llama-3.1-8b-instruct",
                    "--host", "0.0.0.0",
                    "--port", "8000",
                    "--tensor-parallel-size", "1"
                ],
                "volumes": [
                    "/opt/ai-research-platform/models:/models",
                    "/tmp:/tmp"
                ],
                "environment": [
                    "CUDA_VISIBLE_DEVICES=0"
                ],
                "runtime": "nvidia",
                "networks": ["ai-platform"],
                "restart": "unless-stopped"
            }
        },
        "networks": {
            "ai-platform": {
                "external": True
            }
        }
    }

    return docker_config

def create_vllm_bridge_app():
    """Create the main vLLM bridge application file"""

    app_code = '''#!/usr/bin/env python3
"""
vLLM MCP Bridge Application
Main application file for running the vLLM MCP bridge
"""

import uvicorn
from vllm_mcp_config import VLLMRouterMCPBridge

# Create the bridge application
bridge = VLLMRouterMCPBridge()
app = bridge.app

if __name__ == "__main__":
    print("🚀 Starting vLLM MCP Bridge on http://localhost:11011")
    print("📡 OpenAI-compatible endpoint: http://localhost:11011/v1/chat/completions")
    print("🔧 MCP functions endpoint: http://localhost:11011/v1/mcp/functions")

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=11011,
        log_level="info"
    )
'''

    return app_code

def main():
    """Generate all vLLM integration files"""

    print("Generating vLLM MCP integration files...")

    # Create the bridge application
    app_code = create_vllm_bridge_app()
    with open("/home/keith/deepmcp-integration/vllm_mcp_bridge.py", "w") as f:
        f.write(app_code)
    print("✅ Created: /home/keith/deepmcp-integration/vllm_mcp_bridge.py")

    # Create systemd service
    service_content = generate_vllm_systemd_service()
    with open("/home/keith/deepmcp-integration/vllm-mcp-bridge.service", "w") as f:
        f.write(service_content)
    print("✅ Created: /home/keith/deepmcp-integration/vllm-mcp-bridge.service")

    # Create Docker configuration
    docker_config = generate_vllm_docker_config()
    with open("/home/keith/deepmcp-integration/docker-compose.vllm.yml", "w") as f:
        import yaml
        yaml.dump(docker_config, f, default_flow_style=False)
    print("✅ Created: /home/keith/deepmcp-integration/docker-compose.vllm.yml")

    print("\\n🚀 vLLM Integration Setup Complete!")
    print("\\nNext steps:")
    print("1. Start MCP Integration Hub: python mcp_integration_hub.py")
    print("2. Start vLLM MCP Bridge: python vllm_mcp_bridge.py")
    print("3. Access vLLM with MCP at http://localhost:11011/v1/chat/completions")
    print("4. Or install as systemd service: sudo cp vllm-mcp-bridge.service /etc/systemd/system/")