#!/usr/bin/env python3
"""
FortiOS 7.6 Complete API Discovery + SSH CLI Execution Tool
Discovers all available API endpoints and executes CLI commands via SSH
"""

import requests
import json
import paramiko
import sys
from typing import Dict, List, Any, Optional
from urllib.parse import urljoin
import warnings

warnings.filterwarnings('ignore', message='Unverified HTTPS request')


class FortiOSAPIDiscovery:
    """Discover all available FortiOS REST API endpoints"""
    
    def __init__(self, host: str, api_token: str, verify_ssl: bool = False):
        self.host = host
        self.api_token = api_token
        self.verify_ssl = verify_ssl
        self.base_url = f"https://{host}/api/v2"
        self.headers = {
            "Authorization": f"Bearer {api_token}",
            "Accept": "application/json",
            "Content-Type": "application/json"
        }
        
    def discover_cmdb_schema(self) -> Dict[str, Any]:
        """
        Discover all CMDB (configuration) endpoints via schema
        This is the primary self-discovery mechanism
        """
        try:
            url = f"{self.base_url}/cmdb/?action=schema"
            params = {"access_token": self.api_token}
            
            response = requests.get(
                url,
                params=params,
                headers=self.headers,
                verify=self.verify_ssl,
                timeout=30
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                print(f"Error: {response.status_code}")
                print(f"Response: {response.text}")
                return None
                
        except Exception as e:
            print(f"Exception during CMDB schema discovery: {e}")
            return None
    
    def discover_monitor_endpoints(self) -> List[str]:
        """
        Discover available monitor endpoints (note: these may not have schema)
        Monitor endpoints provide real-time system data
        """
        # Common monitor endpoints in FortiOS 7.6
        common_monitor_endpoints = [
            "/api/v2/monitor/system/status",
            "/api/v2/monitor/system/resource",
            "/api/v2/monitor/system/interface",
            "/api/v2/monitor/system/traffic-history",
            "/api/v2/monitor/user/device/query",
            "/api/v2/monitor/firewall/session",
            "/api/v2/monitor/firewall/address",
            "/api/v2/monitor/router/ipv4",
            "/api/v2/monitor/router/ipv6",
            "/api/v2/monitor/switch-controller/detected-device",
            "/api/v2/monitor/system/ha-checksums",
            "/api/v2/monitor/system/ha-peer",
            "/api/v2/monitor/vpn/ipsec",
            "/api/v2/monitor/vpn/l2tp",
            "/api/v2/monitor/vpn/ssl",
            "/api/v2/monitor/user/firewall/auth",
        ]
        return common_monitor_endpoints
    
    def test_monitor_endpoint(self, endpoint: str) -> bool:
        """Test if a monitor endpoint is available"""
        try:
            params = {"access_token": self.api_token}
            response = requests.get(
                f"https://{self.host}{endpoint}",
                params=params,
                headers=self.headers,
                verify=self.verify_ssl,
                timeout=10
            )
            return response.status_code == 200
        except:
            return False
    
    def parse_schema_results(self, schema_data: Dict) -> List[Dict[str, Any]]:
        """
        Parse the schema response to extract endpoint information
        """
        if not schema_data or 'results' not in schema_data:
            return []
        
        endpoints = []
        for result in schema_data['results']:
            endpoint_info = {
                'path': result.get('path', ''),
                'name': result.get('name', ''),
                'mkey': result.get('mkey', None),
                'type': result.get('type', ''),
                'full_url': f"/api/v2/cmdb/{result.get('path', '')}/{result.get('name', '')}",
            }
            endpoints.append(endpoint_info)
        
        return endpoints
    
    def print_discovered_endpoints(self, endpoints: List[Dict[str, Any]]):
        """Pretty print all discovered endpoints"""
        print("\n" + "="*80)
        print("DISCOVERED CMDB ENDPOINTS (Configuration)")
        print("="*80)
        
        organized = {}
        for ep in endpoints:
            path = ep['path']
            if path not in organized:
                organized[path] = []
            organized[path].append(ep)
        
        for path, eps in sorted(organized.items()):
            print(f"\n📁 Path: {path}")
            for ep in eps:
                mkey_info = f" [KEY: {ep['mkey']}]" if ep['mkey'] else ""
                print(f"   └─ {ep['name']}{mkey_info}")
                print(f"      URL: {ep['full_url']}")
    
    def get_endpoint_schema(self, path: str, name: str) -> Dict[str, Any]:
        """Get schema for a specific endpoint"""
        try:
            url = f"{self.base_url}/cmdb/{path}/{name}?action=schema"
            params = {"access_token": self.api_token}
            
            response = requests.get(
                url,
                params=params,
                headers=self.headers,
                verify=self.verify_ssl,
                timeout=30
            )
            
            return response.json() if response.status_code == 200 else None
            
        except Exception as e:
            print(f"Error getting schema for {path}/{name}: {e}")
            return None


class FortiOSSSHExecutor:
    """Execute CLI commands on FortiOS via SSH"""
    
    def __init__(self, host: str, username: str, password: str, port: int = 22):
        self.host = host
        self.username = username
        self.password = password
        self.port = port
        self.client = None
    
    def connect(self) -> bool:
        """Establish SSH connection"""
        try:
            self.client = paramiko.SSHClient()
            self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            self.client.connect(
                self.host,
                port=self.port,
                username=self.username,
                password=self.password,
                timeout=30,
                allow_agent=False,
                look_for_keys=False
            )
            print(f"✅ SSH Connected to {self.host}:{self.port}")
            return True
        except Exception as e:
            print(f"❌ SSH Connection failed: {e}")
            return False
    
    def execute_command(self, command: str) -> Optional[str]:
        """Execute a single CLI command"""
        if not self.client:
            print("❌ Not connected. Call connect() first.")
            return None
        
        try:
            stdin, stdout, stderr = self.client.exec_command(command)
            output = stdout.read().decode('utf-8')
            error = stderr.read().decode('utf-8')
            
            if error:
                print(f"⚠️  Error output: {error}")
            
            return output
        except Exception as e:
            print(f"❌ Command execution failed: {e}")
            return None
    
    def execute_commands_batch(self, commands: List[str]) -> Dict[str, str]:
        """Execute multiple commands and return results"""
        results = {}
        for cmd in commands:
            print(f"\n📤 Executing: {cmd}")
            output = self.execute_command(cmd)
            results[cmd] = output if output else ""
            if output:
                print(f"📥 Output:\n{output}")
        
        return results
    
    def get_arp_table(self) -> Optional[str]:
        """Get ARP table (common diagnostic command)"""
        return self.execute_command("diagnose ip arp list")
    
    def get_device_interfaces(self) -> Optional[str]:
        """Get device interface status"""
        return self.execute_command("get system interface")
    
    def get_routing_table(self) -> Optional[str]:
        """Get routing table"""
        return self.execute_command("get router info routing-table")
    
    def get_system_status(self) -> Optional[str]:
        """Get system status"""
        return self.execute_command("get system status")
    
    def get_dhcp_leases(self) -> Optional[str]:
        """Get DHCP lease list"""
        return self.execute_command("execute dhcp lease-list")
    
    def get_firewall_policies(self) -> Optional[str]:
        """Get firewall policies"""
        return self.execute_command("get firewall policy")
    
    def close(self):
        """Close SSH connection"""
        if self.client:
            self.client.close()
            print("✅ SSH connection closed")


def main():
    """Main demonstration"""
    
    # Configuration
    # Configuration
    FORTIGATE_IP = "192.168.0.254:10443"
    API_TOKEN = "199psNw33b8bq581dNmQqNpkGH53bm"
    SSH_USERNAME = "admin"
    SSH_PASSWORD = "!cg@RW%G@o"
    
    print("=" * 80)
    print("FortiOS 7.6 API Discovery + SSH CLI Execution")
    print("=" * 80)
    
    # ==================== API DISCOVERY ====================
    print("\n[1] DISCOVERING API ENDPOINTS VIA SCHEMA")
    print("-" * 80)
    
    api_discovery = FortiOSAPIDiscovery(FORTIGATE_IP, API_TOKEN)
    
    # Get CMDB schema
    print("🔍 Querying CMDB schema at /api/v2/cmdb/?action=schema...")
    schema = api_discovery.discover_cmdb_schema()
    
    if schema:
        endpoints = api_discovery.parse_schema_results(schema)
        print(f"✅ Discovered {len(endpoints)} CMDB endpoints")
        api_discovery.print_discovered_endpoints(endpoints)
    
    # Test monitor endpoints
    print("\n\n[2] TESTING MONITOR ENDPOINTS")
    print("-" * 80)
    print("🔍 Testing common monitor endpoints...")
    
    monitor_endpoints = api_discovery.discover_monitor_endpoints()
    available_monitors = []
    
    for endpoint in monitor_endpoints:
        if api_discovery.test_monitor_endpoint(endpoint):
            available_monitors.append(endpoint)
            print(f"✅ {endpoint}")
        else:
            print(f"❌ {endpoint}")
    
    # ==================== SSH CLI EXECUTION ====================
    print("\n\n[3] EXECUTING CLI COMMANDS VIA SSH")
    print("-" * 80)
    
    ssh_executor = FortiOSSSHExecutor(FORTIGATE_IP, SSH_USERNAME, SSH_PASSWORD)
    
    if ssh_executor.connect():
        # Execute diagnostic commands
        commands_to_run = [
            "get system status",
            "get system interface",
            "diagnose ip arp list",
            "execute dhcp lease-list",
        ]
        
        results = ssh_executor.execute_commands_batch(commands_to_run)
        
        # Save results
        with open('fortios_cli_output.json', 'w') as f:
            json.dump(results, f, indent=2)
        print("\n✅ Results saved to fortios_cli_output.json")
        
        ssh_executor.close()
    
    # ==================== USAGE EXAMPLES ====================
    print("\n\n[4] PYTHON CODE EXAMPLES")
    print("-" * 80)
    
    examples = '''
# Example 1: Get specific endpoint schema
api = FortiOSAPIDiscovery("172.16.10.1", "token")
schema = api.get_endpoint_schema("firewall", "policy")

# Example 2: Query a specific API endpoint
response = requests.get(
    "https://172.16.10.1/api/v2/cmdb/firewall/policy",
    params={"access_token": "token"},
    verify=False
)
policies = response.json()

# Example 3: Execute CLI command via SSH
ssh = FortiOSSSHExecutor("172.16.10.1", "admin", "password")
ssh.connect()
arp_table = ssh.execute_command("diagnose ip arp list")
print(arp_table)
ssh.close()

# Example 4: Get ARP table via both methods
# Via SSH (more detailed):
arp_ssh = ssh.get_arp_table()

# Via API (if available):
response = requests.get(
    "https://172.16.10.1/api/v2/monitor/system/arp",
    params={"access_token": "token"},
    verify=False
)
    '''
    
    print(examples)


if __name__ == "__main__":
    main()
