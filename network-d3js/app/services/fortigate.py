import asyncio
import json
import httpx
from datetime import datetime, timedelta
from pathlib import Path
from app.utils.paths import DATA_DIR, BASE_DIR

FORTIGATE_URL = "https://192.168.0.254:10443"
API_TOKEN = "199psNw33b8bq581dNmQqNpkGH53bm"
CACHE_FILE = DATA_DIR / "live_network.json"
STALE_AFTER = timedelta(minutes=1) # 1 minute refresh

HEADERS = {"Authorization": f"Bearer {API_TOKEN}"}

# Global validated endpoints
DISCOVERED_ENDPOINTS: dict = {}

async def run_discovery():
    """Probe for valid endpoints to handle version differences."""
    global DISCOVERED_ENDPOINTS
    print("[🔍] Auto-discovering valid API endpoints...")
    
    candidates = {
        "device_query": [
            "/api/v2/monitor/user/device/query",
            "/api/v2/monitor/user/detected-device",
        ],
        "dhcp": [
            "/api/v2/monitor/system/dhcp", 
            "/api/v2/monitor/system/dhcp-server"
        ],
        "interface": [
             "/api/v2/monitor/system/interface",
             "/api/v2/cmdb/system/interface"
        ],
        "switch": [
             "/api/v2/monitor/switch-controller/managed-switch/status"
        ],
        "wifi": [
             "/api/v2/monitor/wifi/client"
        ]
    }

    async with httpx.AsyncClient(verify=False, timeout=5.0) as client:
        for key, paths in candidates.items():
            for path in paths:
                try:
                    r = await client.get(f"{FORTIGATE_URL}{path}", headers=HEADERS)
                    if r.status_code == 200:
                        print(f"   ✅ Found {key}: {path}")
                        DISCOVERED_ENDPOINTS[key] = path
                        break
                except Exception:
                    pass

    if not DISCOVERED_ENDPOINTS:
         print("[⚠️] Discovery failed, falling back to defaults")
         # Fallback to defaults to ensuring loop doesn't break
         DISCOVERED_ENDPOINTS = {
             "device_query": "/api/v2/monitor/user/device/query",
             "dhcp": "/api/v2/monitor/system/dhcp",
             "interface": "/api/v2/monitor/system/interface",
             "switch": "/api/v2/monitor/switch-controller/managed-switch/status", 
             "wifi": "/api/v2/monitor/wifi/client"
         }


async def fetch_fortigate_data() -> dict:
    """Fetch from multiple FortiGate endpoints and merge results."""
    
    # Ensure discovery has run
    if not DISCOVERED_ENDPOINTS:
        await run_discovery()

    async with httpx.AsyncClient(verify=False, timeout=10.0) as client:
        endpoints = list(DISCOVERED_ENDPOINTS.values())
        responses = []
        for ep in endpoints:
            try:
                r = await client.get(f"{FORTIGATE_URL}{ep}", headers=HEADERS)
                if r.status_code == 200:
                    try:
                        data = r.json()
                    except Exception:
                        print(f"[⚠️] {ep} decoding issue, retrying leniently...")
                        content = r.content.decode("utf-8", errors="ignore")
                        try:
                            data = json.loads(content)
                        except json.JSONDecodeError:
                            print(f"[!] {ep} returned invalid JSON")
                            continue

                    results = data.get("results") or data.get("data") or []
                    if results:
                        responses.append(results)
                    else:
                         # print(f"[⚪] {ep} empty") # Reduce noise
                         pass
                else:
                    print(f"[❌] {ep} returned {r.status_code}")
            except Exception as e:
                print(f"[!] Failed to fetch {ep}: {e}")

    nodes = []
    # Flatten responses which is list of lists
    all_entries = [item for sublist in responses for item in sublist]
    
    for entry in all_entries:
        if not isinstance(entry, dict):
            continue
            
        # Normalize fields based on "user/device/query" schema and others
        ip = entry.get("ipv4_address") or entry.get("ip") or entry.get("ip_address") or entry.get("ip_addr") or entry.get("connecting_ip")
        mac = entry.get("mac") or entry.get("mac_address")
        host = entry.get("hostname") or entry.get("name") or "Unknown"
        iface = entry.get("detected_interface") or entry.get("interface") or ""
        
        # Vendor inference
        vendor = entry.get("hardware_vendor") or entry.get("vendor")
        if not vendor and ("fortinet" in (entry.get("os_name") or "").lower()):
            vendor = "Fortinet"

        # Type inference (Priority: Hardware Family > OS Name > Hardware Type > Generic)
        hw_family = entry.get("hardware_family")
        os_name = entry.get("os_name")
        hw_type = entry.get("hardware_type") or entry.get("device_type")
        
        dtype = "device"
        if hw_family:
            dtype = hw_family # e.g. "FortiSwitch", "FortiAP"
        elif os_name:
            dtype = os_name # e.g. "Windows", "Android"
        elif hw_type:
            dtype = hw_type

        # Special handling for Switch Controller data if not caught above
        if "switch_id" in entry or "serial" in entry and entry.get("serial", "").startswith("S"):
             if dtype == "device": dtype = "Switch"
             if not mac and "switch_id" in entry:
                 mac = entry.get("switch_id")
             if not vendor: vendor = "Fortinet"
        
        node_id = mac or ip
        
        if node_id:
            nodes.append({
                "id": node_id,
                "name": host,
                "ip": ip,
                "mac": mac,
                "type": dtype,
                "interface": iface,
                "vendor": vendor,
                "is_online": entry.get("is_online", True)
            })

    # Deduplicate by ID
    seen = {}
    for n in nodes:
        if n["id"] not in seen:
            seen[n["id"]] = n
        else:
            # Update existing with non-empty values
            seen[n["id"]].update({k: v for k, v in n.items() if v})
            
    final_nodes = list(seen.values())
    
    # Add FortiGate core node
    final_nodes.insert(0, {"id": "FortiGate", "name": "FortiGate", "type": "fortigate", "ip": "192.168.0.254", "vendor": "Fortinet"})

    # Links
    links = []
    for n in final_nodes:
        if n["id"] != "FortiGate":
             links.append({"source": "FortiGate", "target": n["id"], "status": "up"})

    return {"timestamp": datetime.now().isoformat(), "nodes": final_nodes, "links": links}

async def update_live_data_if_needed():
    """Refresh the cache file if missing or stale."""
    # Run fetch in background if needed
    if not CACHE_FILE.exists() or is_stale(CACHE_FILE):
        print(f"[⚡] Fetching new FortiGate data (stale > {STALE_AFTER})...")
        try:
            data = await fetch_fortigate_data()
            DATA_DIR.mkdir(parents=True, exist_ok=True)
            with open(CACHE_FILE, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
            print("[✅] live_network.json updated.")
        except Exception as e:
            print(f"[!] Update failed: {e}")
    else:
        print("[⏳] Using cached data.")

def is_stale(path: Path) -> bool:
    mtime = datetime.fromtimestamp(path.stat().st_mtime)
    return datetime.now() - mtime > STALE_AFTER
