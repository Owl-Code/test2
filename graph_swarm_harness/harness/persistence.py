import os
import json
import time
from typing import List
from base_graph.types import Checkpoint
from graph_swarm_harness.core.graph_state import SwarmGraphState

def save_swarm_state(swarm: SwarmGraphState, checkpoint_dir: str) -> str:
    """Serializes the current swarm graph, metadata, and provenance chain, and saves to a JSON file."""
    os.makedirs(checkpoint_dir, exist_ok=True)
    
    ckpt = swarm.checkpoint()
    # Embed harness metadata
    ckpt.metadata["active_goals"] = list(swarm.active_goals)
    ckpt.metadata["goal_energy"] = dict(getattr(swarm, "goal_energy", {}))
    ckpt.metadata["chat_replies"] = list(swarm.chat_replies)
    ckpt.metadata["intra_swarm_messages"] = list(swarm.intra_swarm_messages)
    ckpt.metadata["swarm_name"] = swarm.name
    
    filename = f"checkpoint_{int(time.time())}_{ckpt.checkpoint_id[:8]}.json"
    filepath = os.path.join(checkpoint_dir, filename)
    
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(ckpt.model_dump_json(indent=2))
        
    return filepath

def load_swarm_state(filepath: str) -> SwarmGraphState:
    """Reads a checkpoint file, validates state hashes, and reconstructs the SwarmGraphState."""
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Checkpoint file not found: {filepath}")
        
    with open(filepath, "r", encoding="utf-8") as f:
        data = json.load(f)
        
    ckpt = Checkpoint.model_validate(data)
    
    swarm = SwarmGraphState(name=ckpt.metadata.get("swarm_name", "restored-swarm"))
    # Re-build and verify integrity via base_graph's restore
    swarm.restore(ckpt)
    
    # Reload harness-specific state variables
    swarm.active_goals = ckpt.metadata.get("active_goals", [])
    swarm.goal_energy = ckpt.metadata.get("goal_energy", {})
    swarm.chat_replies = ckpt.metadata.get("chat_replies", [])
    swarm.intra_swarm_messages = ckpt.metadata.get("intra_swarm_messages", [])
    
    return swarm

def checkpoint_to_dict(swarm: SwarmGraphState) -> dict:
    """Converts the swarm graph state to a dictionary representation for database storage."""
    ckpt = swarm.checkpoint()
    ckpt.metadata["active_goals"] = list(swarm.active_goals)
    ckpt.metadata["goal_energy"] = dict(getattr(swarm, "goal_energy", {}))
    ckpt.metadata["chat_replies"] = list(swarm.chat_replies)
    ckpt.metadata["intra_swarm_messages"] = list(swarm.intra_swarm_messages)
    ckpt.metadata["swarm_name"] = swarm.name
    return ckpt.model_dump()

def restore_swarm_from_dict(data: dict) -> SwarmGraphState:
    """Reconstructs a SwarmGraphState from a serialized dictionary and verifies integrity."""
    ckpt = Checkpoint.model_validate(data)
    swarm = SwarmGraphState(name=ckpt.metadata.get("swarm_name", "restored-swarm"))
    swarm.restore(ckpt)
    swarm.active_goals = ckpt.metadata.get("active_goals", [])
    swarm.goal_energy = ckpt.metadata.get("goal_energy", {})
    swarm.chat_replies = ckpt.metadata.get("chat_replies", [])
    swarm.intra_swarm_messages = ckpt.metadata.get("intra_swarm_messages", [])
    return swarm

def list_checkpoints(checkpoint_dir: str) -> List[str]:
    """Lists all available JSON checkpoint files sorted from newest to oldest."""
    if not os.path.exists(checkpoint_dir):
        return []
        
    files = [
        os.path.join(checkpoint_dir, f)
        for f in os.listdir(checkpoint_dir)
        if f.startswith("checkpoint_") and f.endswith(".json")
    ]
    # Sort by modification time descending
    files.sort(key=os.path.getmtime, reverse=True)
    return files
