# app/main.py
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path
import asyncio
import json

from app.services.fortigate import update_live_data_if_needed, fetch_fortigate_data
from app.utils.paths import DATA_DIR, STATIC_DIR

app = FastAPI(title="FortiGate Network Topology API")

# Mount static directories
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
app.mount("/icons", StaticFiles(directory=Path("/home/keith/network-d3js/icons")), name="icons")

# Connected WebSocket clients
active_clients = set()

@app.get("/")
async def index():
    """Serve main dashboard."""
    index_path = STATIC_DIR / "index.html"
    return HTMLResponse(index_path.read_text())

@app.get("/api/live")
async def get_live_data():
    """Serve latest cached JSON."""
    data_path = DATA_DIR / "live_network.json"
    await update_live_data_if_needed()
    if data_path.exists():
        return FileResponse(data_path, media_type="application/json")
    return JSONResponse({"error": "No data yet."}, status_code=404)

@app.websocket("/ws/live")
async def websocket_endpoint(websocket: WebSocket):
    """Push live topology updates to D3.js clients."""
    await websocket.accept()
    active_clients.add(websocket)
    print(f"🔌 Client connected: {len(active_clients)} total")

    try:
        while True:
            # Wait for message (client may send pings)
            await websocket.receive_text()
    except WebSocketDisconnect:
        active_clients.remove(websocket)
        print(f"❌ Client disconnected ({len(active_clients)} left)")

@app.on_event("startup")
async def background_updater():
    """Runs periodically to fetch & broadcast updates."""
    async def loop():
        while True:
            try:
                data = await fetch_fortigate_data()
                DATA_DIR.mkdir(exist_ok=True)
                file_path = DATA_DIR / "live_network.json"
                file_path.write_text(json.dumps(data, indent=2))
                print("🛰 Broadcast update to", len(active_clients), "clients")

                # Send to connected browsers
                for ws in list(active_clients):
                    try:
                        await ws.send_json(data)
                    except Exception:
                        active_clients.discard(ws)
            except Exception as e:
                print("⚠️ Update loop error:", e)

            await asyncio.sleep(30)  # every 30 seconds
    asyncio.create_task(loop())
