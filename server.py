import os
import sys
import asyncio
from typing import List, Dict, Any
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, BackgroundTasks
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

# Ensure current workspace directory is in system path for clean imports
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from graph_swarm_harness.harness.main_loop import SwarmHarnessOrchestrator
from graph_swarm_harness.core.emergence import calculate_swarm_emergence

app = FastAPI(title="Graph Swarm Harness Dashboard")

# Initialize Swarm Orchestrator
orchestrator = SwarmHarnessOrchestrator(config_path="graph_swarm_harness/config.yaml")
orchestrator.setup_swarm(resume=False)

# When run via the Web Dashboard, auto-confirm is enabled by default to prevent blocking on background workers
orchestrator.agent_executor.auto_confirm = True

# Track active websocket connections
active_connections: List[WebSocket] = []

class GoalPayload(BaseModel):
    goal: str

class ConfigPayload(BaseModel):
    max_active_agents_per_tick: int

class RoleTemplatePayload(BaseModel):
    role: str
    skills: List[str]
    tools: List[str]
    persona: str

def get_swarm_state_payload() -> Dict[str, Any]:
    """Compiles the complete visual and metrics state of the swarm."""
    swarm = orchestrator.swarm
    agents = []
    for a in swarm.get_agents():
        agents.append({
            "id": a.id,
            "role": a.role,
            "energy": a.energy,
            "opinion": a.node.opinions.get("main", 0.0),
            "emergence": a.emergence_level,
            "skills": list(a.active_skills),
            "tools": list(a.available_tools),
            "last_thought": a.node.local_memory.get("last_decision_reason", "Idling..."),
            "last_result": a.node.local_memory.get("last_action_result", "None"),
            "is_active": a.node.state.get("is_active", False),
            "mode": a.node.control_mode.value
        })
        
    edges = []
    for e in swarm.graph.edges.values():
        edges.append({
            "id": e.id,
            "source": e.source_id,
            "target": e.target_id,
            "weight": e.weight,
            "strength": e.strength,
            "type": e.edge_type.value
        })
        
    audit = []
    for rec in swarm.provenance.chain[-8:]:
        audit.append({
            "index": rec.index,
            "actor": rec.delta.actor,
            "operation": rec.delta.operation,
            "target": rec.delta.target,
            "hash": rec.current_hash[:16]
        })
        
    return {
        "name": swarm.name,
        "step_index": swarm.step_index,
        "emergence_level": calculate_swarm_emergence(swarm),
        "active_goals": [{"text": g, "energy": getattr(swarm, "goal_energy", {}).get(g, 100.0)} for g in swarm.active_goals],
        "provenance_valid": swarm.provenance.verify_chain(),
        "agents": agents,
        "edges": edges,
        "audit_trail": audit,
        "role_templates": swarm.role_templates,
        "chat_replies": list(swarm.chat_replies),
        "intra_swarm_messages": list(getattr(swarm, "intra_swarm_messages", [])),
        "max_active_agents_per_tick": orchestrator.config.get("max_active_agents_per_tick", 2)
    }

async def broadcast_state():
    """Broadcasts current state payload to all active WebSocket connections."""
    payload = get_swarm_state_payload()
    for ws in list(active_connections):
        try:
            await ws.send_json({"type": "state", "data": payload})
        except Exception:
            if ws in active_connections:
                active_connections.remove(ws)

# Mount static frontend assets
static_dir = os.path.join("graph_swarm_harness", "harness", "dashboard_assets")
os.makedirs(static_dir, exist_ok=True)
app.mount("/static", StaticFiles(directory=static_dir), name="static")

@app.get("/")
def get_index():
    return FileResponse(os.path.join(static_dir, "index.html"))

@app.get("/api/state")
def get_state():
    return get_swarm_state_payload()

@app.post("/api/tick")
async def run_tick():
    log_summary = await orchestrator.run_tick()
    await broadcast_state()
    return {"status": "success", "log": log_summary}

@app.post("/api/goal")
async def add_goal(payload: GoalPayload):
    swarm = orchestrator.swarm
    if payload.goal not in swarm.active_goals:
        swarm.active_goals.append(payload.goal)
    if not hasattr(swarm, "goal_energy"):
        swarm.goal_energy = {}
    swarm.goal_energy[payload.goal] = 100.0
    
    swarm.provenance.add_mutation(
        actor="operator",
        operation="inject_goal",
        target=payload.goal,
        before=None,
        after=payload.goal
    )
    await broadcast_state()
    return {"status": "success", "active_goals": [{"text": g, "energy": swarm.goal_energy.get(g, 100.0)} for g in swarm.active_goals]}

class GoalDeletePayload(BaseModel):
    goal: str

@app.post("/api/goal/delete")
async def delete_goal(payload: GoalDeletePayload):
    swarm = orchestrator.swarm
    if payload.goal in swarm.active_goals:
        swarm.active_goals.remove(payload.goal)
        if hasattr(swarm, "goal_energy") and payload.goal in swarm.goal_energy:
            del swarm.goal_energy[payload.goal]
            
        swarm.provenance.add_mutation(
            actor="operator",
            operation="delete_goal",
            target=payload.goal,
            before=payload.goal,
            after=None
        )
        await broadcast_state()
        return {"status": "success", "active_goals": [{"text": g, "energy": swarm.goal_energy.get(g, 100.0)} for g in swarm.active_goals]}
    return {"status": "error", "message": "Goal not found in active list."}

@app.get("/api/roles")
def get_roles():
    return orchestrator.swarm.role_templates

@app.post("/api/roles")
async def update_role(payload: RoleTemplatePayload):
    orchestrator.swarm.update_role_template(
        role=payload.role,
        config={
            "skills": payload.skills,
            "tools": payload.tools,
            "persona": payload.persona
        }
    )
    await broadcast_state()
    return {"status": "success", "role_templates": orchestrator.swarm.role_templates}

@app.post("/api/config")
async def update_config(payload: ConfigPayload):
    orchestrator.config["max_active_agents_per_tick"] = payload.max_active_agents_per_tick
    await broadcast_state()
    return {"status": "success", "max_active_agents_per_tick": orchestrator.config["max_active_agents_per_tick"]}

# Background continuous loop state
is_running = False

async def continuous_loop_task(delay: float):
    global is_running
    while is_running:
        await orchestrator.run_tick()
        await broadcast_state()
        await asyncio.sleep(delay)

@app.post("/api/loop/start")
async def start_loop(delay: float = 3.0):
    global is_running
    if not is_running:
        is_running = True
        asyncio.create_task(continuous_loop_task(delay))
    return {"status": "running"}

@app.post("/api/loop/stop")
def stop_loop():
    global is_running
    is_running = False
    return {"status": "stopped"}

class RollbackPayload(BaseModel):
    tick: int

class FileWritePayload(BaseModel):
    path: str
    content: str

@app.get("/api/history")
def get_history_list():
    return orchestrator.history_db.get_history()

@app.post("/api/history/rollback")
async def rollback_history(payload: RollbackPayload):
    try:
        msg = orchestrator.rollback_to_tick(payload.tick)
        await broadcast_state()
        return {"status": "success", "message": msg}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.get("/api/files/list")
def list_workspace_files():
    root = os.path.abspath(orchestrator.workspace_root)
    file_tree = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if not d.startswith(".") and d not in ("__pycache__", "artifacts")]
        for filename in filenames:
            if filename.startswith(".") or filename.endswith(".pyc"):
                continue
            full_path = os.path.join(dirpath, filename)
            rel_path = os.path.relpath(full_path, root)
            file_tree.append(rel_path.replace("\\", "/"))
    return sorted(file_tree)

@app.get("/api/files/read")
def read_workspace_file(path: str):
    from graph_swarm_harness.tools.core_tool_implementations import _check_path_safety
    try:
        safe_path = _check_path_safety(path, orchestrator.workspace_root)
        if not os.path.exists(safe_path):
            return {"status": "error", "message": "File not found"}
        with open(safe_path, "r", encoding="utf-8") as f:
            return {"status": "success", "content": f.read()}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.post("/api/files/write")
def write_workspace_file(payload: FileWritePayload):
    from graph_swarm_harness.tools.core_tool_implementations import _check_path_safety
    try:
        safe_path = _check_path_safety(payload.path, orchestrator.workspace_root)
        os.makedirs(os.path.dirname(safe_path), exist_ok=True)
        with open(safe_path, "w", encoding="utf-8") as f:
            f.write(payload.content)
        return {"status": "success"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

class ChatSendPayload(BaseModel):
    message: str

async def run_background_tick():
    await orchestrator.run_tick()
    await broadcast_state()

@app.post("/api/chat/send")
async def send_chat_message(payload: ChatSendPayload, background_tasks: BackgroundTasks):
    import time
    swarm = orchestrator.swarm
    
    # 1. Append operator's message to chat logs
    swarm.chat_replies.append({
        "sender": "operator",
        "text": payload.message,
        "timestamp": int(time.time())
    })
    
    # 2. Route to coordinator agent's inbox
    coordinator = next((a for a in swarm.get_agents() if a.role == "coordinator"), None)
    if not coordinator:
        agents = swarm.get_agents()
        if agents:
            coordinator = agents[0]
            
    if coordinator:
        coordinator.receive_message(sender_id="operator", message=payload.message)
        
        # 3. Step the swarm in background task so HTTP returns instantly
        background_tasks.add_task(run_background_tick)
    else:
        swarm.chat_replies.append({
            "sender": "system",
            "text": "Warning: No active agents found in the swarm to process your message.",
            "timestamp": int(time.time())
        })
        
    await broadcast_state()
    return {"status": "success", "chat_replies": swarm.chat_replies}

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    active_connections.append(websocket)
    try:
        await websocket.send_json({"type": "state", "data": get_swarm_state_payload()})
        while True:
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        if websocket in active_connections:
            active_connections.remove(websocket)
