#!/usr/bin/env python3
"""
OpenWebUI MCP Integration Configuration
Provides function calling integration for OpenWebUI to use MCP servers
"""

import json
import os
from typing import Dict, List, Any

def generate_openwebui_functions_file():
    """
    Generate OpenWebUI functions.py file for MCP integration
    This file should be placed in OpenWebUI's functions directory
    """

    functions_code = '''"""
MCP Functions for OpenWebUI
Auto-generated MCP server integration functions for OpenWebUI
"""

import json
import httpx
from datetime import datetime
from typing import Dict, List, Any, Optional
from pydantic import BaseModel

# MCP Integration Hub endpoint
MCP_HUB_URL = "http://localhost:11010"

class Tools:
    """MCP Tools integration for OpenWebUI"""

    def __init__(self):
        self.name = "mcp_tools"
        self.description = "Access MCP (Model Context Protocol) tools and servers"

    async def get_current_time(
        self,
        timezone: str = "UTC",
        user_message: str = "",
        __user__: dict = {},
        __event_emitter__=None
    ) -> str:
        """
        Get the current date and time in specified timezone

        :param timezone: Timezone (e.g., 'UTC', 'America/New_York')
        :return: Current time information
        """
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    f"{MCP_HUB_URL}/openwebui/execute",
                    json={
                        "name": "get_current_time",
                        "arguments": {"timezone": timezone}
                    }
                )
                result = response.json()

                if result["success"]:
                    time_data = result["result"]
                    return f"Current time in {timezone}: {time_data['datetime']} ({time_data['day_of_week']})"
                else:
                    return f"Error getting time: {result.get('error', 'Unknown error')}"

            except Exception as e:
                return f"Failed to get current time: {str(e)}"

    async def git_log(
        self,
        repo_path: str,
        max_commits: int = 10,
        user_message: str = "",
        __user__: dict = {},
        __event_emitter__=None
    ) -> str:
        """
        Get git commit history for a repository

        :param repo_path: Path to git repository
        :param max_commits: Maximum number of commits to return
        :return: Git commit history
        """
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    f"{MCP_HUB_URL}/openwebui/execute",
                    json={
                        "name": "git_log",
                        "arguments": {
                            "repo_path": repo_path,
                            "max_commits": max_commits
                        }
                    }
                )
                result = response.json()

                if result["success"]:
                    git_data = result["result"]
                    commits = git_data["commits"]

                    output = f"Git log for {repo_path} (showing {len(commits)} commits):\\n\\n"
                    for commit in commits:
                        output += f"• {commit['hash']}: {commit['message']} by {commit['author']}\\n"

                    return output
                else:
                    return f"Error getting git log: {result.get('error', 'Unknown error')}"

            except Exception as e:
                return f"Failed to get git log: {str(e)}"

    async def read_file(
        self,
        path: str,
        user_message: str = "",
        __user__: dict = {},
        __event_emitter__=None
    ) -> str:
        """
        Read contents of a file

        :param path: File path to read
        :return: File contents
        """
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    f"{MCP_HUB_URL}/openwebui/execute",
                    json={
                        "name": "read_file",
                        "arguments": {"path": path}
                    }
                )
                result = response.json()

                if result["success"]:
                    file_data = result["result"]
                    return f"File: {file_data['path']}\\nSize: {file_data['size']} bytes\\nModified: {file_data['modified']}\\n\\nContent:\\n{file_data['content']}"
                else:
                    return f"Error reading file: {result.get('error', 'Unknown error')}"

            except Exception as e:
                return f"Failed to read file: {str(e)}"

    async def create_memory_entity(
        self,
        name: str,
        entity_type: str,
        observations: List[str] = None,
        user_message: str = "",
        __user__: dict = {},
        __event_emitter__=None
    ) -> str:
        """
        Create a new entity in the knowledge graph memory

        :param name: Entity name
        :param entity_type: Type of entity
        :param observations: List of observations about the entity
        :return: Created entity information
        """
        if observations is None:
            observations = []

        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    f"{MCP_HUB_URL}/openwebui/execute",
                    json={
                        "name": "create_entity",
                        "arguments": {
                            "name": name,
                            "entity_type": entity_type,
                            "observations": observations
                        }
                    }
                )
                result = response.json()

                if result["success"]:
                    entity_data = result["result"]
                    return f"Created entity '{entity_data['name']}' (ID: {entity_data['entity_id']})\\nType: {entity_data['type']}\\nObservations: {len(entity_data['observations'])}\\nCreated: {entity_data['created']}"
                else:
                    return f"Error creating entity: {result.get('error', 'Unknown error')}"

            except Exception as e:
                return f"Failed to create entity: {str(e)}"

    async def get_network_status(
        self,
        organization: str = "all",
        device_type: str = "all",
        user_message: str = "",
        __user__: dict = {},
        __event_emitter__=None
    ) -> str:
        """
        Get comprehensive status of Fortinet network infrastructure

        :param organization: Organization ID or 'all'
        :param device_type: Type of devices to query ('fortigate', 'fortiswitch', or 'all')
        :return: Network status information
        """
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    f"{MCP_HUB_URL}/openwebui/execute",
                    json={
                        "name": "get_network_status",
                        "arguments": {
                            "organization": organization,
                            "device_type": device_type
                        }
                    }
                )
                result = response.json()

                if result["success"]:
                    network_data = result["result"]
                    devices = network_data["devices"]

                    return f"""Network Status for {organization}:
• Device Type Filter: {device_type}
• Overall Status: {network_data['status']}
• Security Fabric: {network_data['security_fabric']}

Device Counts:
• FortiGate devices: {devices['fortigate']}
• FortiSwitch devices: {devices['fortiswitch']}
• Online devices: {devices['online']}
• Offline devices: {devices['offline']}"""
                else:
                    return f"Error getting network status: {result.get('error', 'Unknown error')}"

            except Exception as e:
                return f"Failed to get network status: {str(e)}"

    async def configure_firewall_policy(
        self,
        device_id: str,
        policy_name: str,
        action: str,
        source_zone: str = "",
        destination_zone: str = "",
        user_message: str = "",
        __user__: dict = {},
        __event_emitter__=None
    ) -> str:
        """
        Create or modify firewall policies on FortiGate devices

        :param device_id: FortiGate device identifier
        :param policy_name: Name for the firewall policy
        :param action: Action for the policy ('allow' or 'deny')
        :param source_zone: Source security zone
        :param destination_zone: Destination security zone
        :return: Policy creation result
        """
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    f"{MCP_HUB_URL}/openwebui/execute",
                    json={
                        "name": "configure_firewall_policy",
                        "arguments": {
                            "device_id": device_id,
                            "policy_name": policy_name,
                            "action": action,
                            "source_zone": source_zone,
                            "destination_zone": destination_zone
                        }
                    }
                )
                result = response.json()

                if result["success"]:
                    policy_data = result["result"]
                    return f"""Firewall Policy Created Successfully:
• Policy ID: {policy_data['policy_id']}
• Device: {policy_data['device_id']}
• Policy Name: {policy_data['policy_name']}
• Action: {policy_data['action']}
• Status: {policy_data['status']}
• Created: {policy_data['created']}"""
                else:
                    return f"Error configuring firewall policy: {result.get('error', 'Unknown error')}"

            except Exception as e:
                return f"Failed to configure firewall policy: {str(e)}"
'''

    return functions_code

def generate_openwebui_docker_config():
    """
    Generate Docker Compose configuration for OpenWebUI with MCP integration
    """

    docker_config = {
        "version": "3.8",
        "services": {
            "mcp-integration-hub": {
                "build": {
                    "context": "/home/keith/deepmcp-integration",
                    "dockerfile": "Dockerfile"
                },
                "ports": ["11010:11010"],
                "volumes": [
                    "/home/keith/chat-copilot/mcp-servers:/mcp-servers:ro"
                ],
                "environment": [
                    "MCP_SERVERS_PATH=/mcp-servers"
                ],
                "networks": ["ai-platform"],
                "restart": "unless-stopped"
            },
            "openwebui-with-mcp": {
                "image": "ghcr.io/open-webui/open-webui:main",
                "ports": ["11001:8080"],
                "volumes": [
                    "openwebui_data:/app/backend/data",
                    "/home/keith/deepmcp-integration:/app/backend/functions/mcp:ro"
                ],
                "environment": [
                    "OPENAI_API_BASE_URL=http://localhost:11002/v1",
                    "OPENAI_API_KEY=dummy-key",
                    "ENABLE_FUNCTION_CALLING=true",
                    "MCP_HUB_URL=http://mcp-integration-hub:11010"
                ],
                "depends_on": ["mcp-integration-hub"],
                "networks": ["ai-platform"],
                "restart": "unless-stopped"
            }
        },
        "volumes": {
            "openwebui_data": {}
        },
        "networks": {
            "ai-platform": {
                "external": True
            }
        }
    }

    return docker_config

def main():
    """Generate all OpenWebUI integration files"""

    # Create OpenWebUI functions file
    print("Generating OpenWebUI functions file...")
    functions_code = generate_openwebui_functions_file()

    with open("/home/keith/deepmcp-integration/openwebui_functions.py", "w") as f:
        f.write(functions_code)

    print("✅ Created: /home/keith/deepmcp-integration/openwebui_functions.py")

    # Create Docker Compose configuration
    print("Generating OpenWebUI Docker configuration...")
    docker_config = generate_openwebui_docker_config()

    with open("/home/keith/deepmcp-integration/docker-compose.openwebui.yml", "w") as f:
        import yaml
        yaml.dump(docker_config, f, default_flow_style=False)

    print("✅ Created: /home/keith/deepmcp-integration/docker-compose.openwebui.yml")

    print("\\n🚀 OpenWebUI Integration Setup Complete!")
    print("\\nNext steps:")
    print("1. Start MCP Integration Hub: python mcp_integration_hub.py")
    print("2. Copy openwebui_functions.py to your OpenWebUI functions directory")
    print("3. Start OpenWebUI with function calling enabled")
    print("4. Access OpenWebUI at http://localhost:11001")

if __name__ == "__main__":
    main()