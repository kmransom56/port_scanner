#!/usr/bin/env python3
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
