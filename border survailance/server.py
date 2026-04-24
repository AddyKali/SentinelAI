import asyncio
import json
import os
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, HTMLResponse
from pydantic import BaseModel
from typing import List

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"],
                   allow_methods=["*"], allow_headers=["*"])

shared_state = {
    "frame":          None,
    "alerts":         [],
    "zones":          [],
    "total_persons":  0,
    "total_vehicles": 0,
    "night":          False,
    "surge":          False,
    "modes":          {'loitering': True, 'night': True, 'surge': True},
    "setup_done":     False,
    "current_source": "VIDEO",
}
pending_commands = []

class ZoneData(BaseModel):
    name: str
    points: List[List[int]]

class TripwireData(BaseModel):
    name: str
    p1: List[int]
    p2: List[int]

class ModeData(BaseModel):
    mode: str
    value: bool

class SourceData(BaseModel):
    source: str

@app.post("/add_zone")
def add_zone(zone: ZoneData):
    pending_commands.append({'type': 'add_zone', 'data': zone.dict()})
    return {"status": "ok"}

@app.post("/add_tripwire")
def add_tripwire(tw: TripwireData):
    pending_commands.append({'type': 'add_tripwire', 'data': tw.dict()})
    return {"status": "ok"}

@app.post("/start_detection")
def start_detection():
    pending_commands.append({'type': 'start_detection'})
    shared_state["setup_done"] = True
    return {"status": "ok"}

@app.post("/stop_detection")
def stop_detection():
    pending_commands.append({'type': 'stop_detection'})
    shared_state["setup_done"] = False
    return {"status": "ok"}

@app.post("/set_mode")
def set_mode(data: ModeData):
    pending_commands.append({'type': 'set_mode', 'mode': data.mode, 'value': data.value})
    return {"status": "ok"}

@app.post("/switch_source")
def switch_source(data: ModeData):
    is_live = data.value
    pending_commands.append({'type': 'switch_source', 'value': is_live})
    shared_state["current_source"] = "LIVE" if is_live else "VIDEO"
    return {"status": "ok", "source": shared_state["current_source"]}

@app.post("/change_source")
def change_source(data: SourceData):
    src = data.source.strip()
    is_live = src.startswith("http") or src.startswith("rtsp")
    pending_commands.append({'type': 'change_source', 'source': src, 'value': is_live})
    shared_state["current_source"] = src if is_live else src
    return {"status": "ok", "source": src}

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            await asyncio.sleep(0.05)
            if shared_state["frame"]:
                await websocket.send_text(json.dumps(shared_state))
    except WebSocketDisconnect:
        pass

# ── Mobile page ────────────────────────────────────────────────────────────────
MOBILE_PATH = os.path.join(os.path.dirname(__file__), "mobile.html")

@app.get("/mobile")
def serve_mobile():
    if os.path.exists(MOBILE_PATH):
        return FileResponse(MOBILE_PATH)
    return HTMLResponse("<h1>mobile.html not found. Put mobile.html in border survailance folder.</h1>")

# ── Static (React dashboard) ───────────────────────────────────────────────────
STATIC_PATH = os.path.join(os.path.dirname(__file__), "static")
if os.path.exists(STATIC_PATH):
    app.mount("/static",
              StaticFiles(directory=os.path.join(STATIC_PATH, "static")),
              name="static")

@app.get("/")
def serve_react():
    return FileResponse(os.path.join(STATIC_PATH, "index.html"))

@app.get("/{full_path:path}")
def catch_all(full_path: str):
    if full_path == "mobile":
        return serve_mobile()
    index = os.path.join(STATIC_PATH, "index.html")
    if os.path.exists(index):
        return FileResponse(index)
    return HTMLResponse("Not found", status_code=404)
