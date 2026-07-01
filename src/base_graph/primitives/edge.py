from dataclasses import dataclass, field
import time
from typing import Any, Dict, Optional, Union
from base_graph.types import EdgeType

@dataclass
class AdaptiveEdge:
    source_id: str
    target_id: str
    weight: float = 1.0
    edge_type: EdgeType = EdgeType.COMMUNICATION
    strength: float = 1.0  # Antifragility accumulator: increases under beneficial stress (usage)
    last_updated: float = field(default_factory=time.time)
    usage_count: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def id(self) -> str:
        return f"{self.source_id}->{self.target_id}"

    def update_weight(self, delta: float, reason: str, provenance_record: Optional[Dict[str, Any]] = None) -> None:
        """Updates edge weight and increases usage_count and strength (antifragility)."""
        self.weight = max(0.0, self.weight + delta)
        self.usage_count += 1
        
        # Antifragile adaptation: usage increases the edge's structural capacity (strength)
        self.strength = min(10.0, self.strength + 0.1 * abs(delta))
        self.last_updated = time.time()
        
        history = self.metadata.setdefault("update_history", [])
        history.append({
            "timestamp": self.last_updated,
            "delta": delta,
            "reason": reason,
            "strength": self.strength
        })

    def propagate(self, value: Any, decay: float = 0.9) -> Any:
        """Propagates a signal value down the edge, subject to decay and scaling by strength/weight."""
        self.usage_count += 1
        # Edge strength/weight buffers decay
        effective_decay = decay / (1.0 + 0.05 * (self.strength - 1.0))
        
        if isinstance(value, (int, float)):
            propagated_val = value * self.weight * (1.0 - effective_decay)
        else:
            propagated_val = value
            
        self.metadata["last_propagated_value"] = propagated_val
        self.last_updated = time.time()
        return propagated_val

@dataclass
class EmergenceEdge(AdaptiveEdge):
    emergence_flow: float = 0.0
    diffusion_potential: float = 0.0

    def decay_flow(self, decay_rate: float = 0.1) -> None:
        """Simulates flow evaporation over time (stigmergic pheromone evaporation)."""
        self.emergence_flow = max(0.0, self.emergence_flow * (1.0 - decay_rate))
        self.weight = max(0.1, self.weight * (1.0 - 0.5 * decay_rate))

@dataclass
class TrophallaxisEdge(AdaptiveEdge):
    def __post_init__(self) -> None:
        self.edge_type = EdgeType.TROPHALLAXIS

    def transfer(self, from_node: Any, to_node: Any, resource: str, amount: float) -> bool:
        """Performs resource exchange between nodes with balance checks and homeostasis feedback.
        
        from_node and to_node are expected to be instances of EmergenceNode.
        """
        # Ensure we have correct nodes
        if from_node.id != self.source_id or to_node.id != self.target_id:
            return False

        # Safety check: from_node must have sufficient resources and exceed threshold
        available = from_node.resources.get(resource, 0.0)
        safety_threshold = from_node.local_memory.get("homeostasis_safety_threshold", 20.0)

        if available - amount < safety_threshold:
            # Transfer amount capped or aborted to protect provider node survival
            amount = max(0.0, available - safety_threshold)
            if amount <= 0:
                # Log denial due to self-preservation
                from_node.local_memory.setdefault("denied_transfers", []).append({
                    "to": to_node.id, "resource": resource, "requested": amount
                })
                return False

        # Apply transfer
        from_node.resources[resource] = available - amount
        to_node.receive_trophallaxis(resource, amount, from_node.id)

        # Update edge attributes (increases edge strength)
        self.update_weight(
            delta=0.05 * amount,
            reason=f"Trophallaxis transfer of {amount} {resource}",
            provenance_record={"actor": from_node.id, "action": "trophallaxis"}
        )
        return True
