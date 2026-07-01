from enum import Enum
from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, Field
from uuid import UUID

class ControlMode(str, Enum):
    HIERARCHICAL = "HIERARCHICAL"
    DECENTRALIZED = "DECENTRALIZED"
    STIGMERGIC = "STIGMERGIC"
    EMERGENCE = "EMERGENCE"

class EdgeType(str, Enum):
    COMMUNICATION = "COMMUNICATION"
    COMMAND = "COMMAND"
    RESOURCE = "RESOURCE"
    INFLUENCE = "INFLUENCE"
    STIGMERGY = "STIGMERGY"
    TROPHALLAXIS = "TROPHALLAXIS"

class Action(BaseModel):
    action_type: str
    target_id: Optional[str] = None
    parameters: Dict[str, Any] = Field(default_factory=dict)

class Decision(BaseModel):
    node_id: str
    selected_action: Action
    confidence: float
    reason: str
    metadata: Dict[str, Any] = Field(default_factory=dict)

class SwarmHealthReport(BaseModel):
    emergence_level: float
    spectral_gap: float
    diffusion_entropy: float
    resource_balance: float
    provenance_integrity: bool
    antifragility_score: float
    node_count: int
    edge_count: int
    metadata: Dict[str, Any] = Field(default_factory=dict)

class SwarmStepResult(BaseModel):
    step_index: int
    active_modes: Dict[str, int]
    decisions: Dict[str, Decision]
    health: SwarmHealthReport
    provenance_hash: str

class StateDelta(BaseModel):
    timestamp: float
    actor: str
    operation: str
    target: str
    before: Any
    after: Any
    meta: Dict[str, Any] = Field(default_factory=dict)

class ProvenanceRecord(BaseModel):
    index: int
    timestamp: float
    delta: StateDelta
    previous_hash: str
    current_hash: str

class Checkpoint(BaseModel):
    timestamp: float
    checkpoint_id: str
    state_hash: str
    nodes_state: List[Dict[str, Any]]
    edges_state: List[Dict[str, Any]]
    provenance_chain: List[Dict[str, Any]]
    metadata: Dict[str, Any] = Field(default_factory=dict)
