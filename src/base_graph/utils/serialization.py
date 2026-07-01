import json
from typing import Any, Dict
from uuid import UUID
from pydantic import BaseModel

try:
    import numpy as np
except ImportError:
    np = None  # type: ignore

class SwarmStateEncoder(json.JSONEncoder):
    """Custom JSON encoder to serialize NumPy values, UUIDs, sets, and Pydantic models."""
    def default(self, obj: Any) -> Any:
        if isinstance(obj, UUID):
            return str(obj)
        if isinstance(obj, set):
            return sorted(list(obj))
        if isinstance(obj, BaseModel):
            return obj.model_dump()
        if np is not None:
            if isinstance(obj, np.integer):
                return int(obj)
            if isinstance(obj, np.floating):
                return float(obj)
            if isinstance(obj, np.ndarray):
                return obj.tolist()
        return super().default(obj)

def serialize_state(state: Any) -> str:
    """Safely serializes custom swarm data states into standard JSON text."""
    return json.dumps(state, cls=SwarmStateEncoder, sort_keys=True)

def deserialize_state(json_str: str) -> Any:
    """Restores serialized data structures from a JSON string representation."""
    return json.loads(json_str)
