from dataclasses import dataclass, field
import uuid
from typing import Any, Dict, List, Optional, Union, Callable
from uuid import UUID

from base_graph.types import ControlMode, Action, Decision

@dataclass
class BaseNode:
    id: Union[str, UUID]
    state: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class EmergenceNode(BaseNode):
    local_memory: Dict[str, Any] = field(default_factory=dict)
    resources: Dict[str, float] = field(default_factory=dict)
    opinions: Dict[str, float] = field(default_factory=dict)
    goals: List[Any] = field(default_factory=list)
    control_mode: ControlMode = ControlMode.EMERGENCE
    policy: Optional[Callable[[ "EmergenceNode", List[Action], Dict[str, Any] ], Decision]] = None

    def __post_init__(self) -> None:
        if isinstance(self.id, str):
            try:
                self.id = str(UUID(self.id))
            except ValueError:
                # Keep original string if not a valid UUID format
                pass
        else:
            self.id = str(self.id)
        
        # Ensure default resources are initialized
        if "energy" not in self.resources:
            self.resources["energy"] = 100.0

    def local_step(self, context: Dict[str, Any]) -> Action:
        """Runs one atomic local step of the node to choose its next action.
        
        Context dict typically includes:
          - neighbors: List of connected nodes or node states
          - local_edges: List of edges incident to this node
          - global_time: float or int
        """
        # Formulate available action space
        action_space = [
            Action(action_type="IDLE", parameters={}),
            Action(action_type="SEARCH_RESOURCE", parameters={}),
            Action(action_type="SHARE_RESOURCE", parameters={"amount": 5.0}),
            Action(action_type="CONVERGE_OPINION", parameters={}),
        ]
        
        # Route decision through the policy
        decision = self.decide(action_space, context)
        
        # Apply local changes based on action if appropriate
        action = decision.selected_action
        if action.action_type == "SHARE_RESOURCE":
            target = action.parameters.get("target_id")
            amount = action.parameters.get("amount", 0.0)
            if target and self.resources.get("energy", 0.0) >= amount:
                self.resources["energy"] -= amount
                
        self.local_memory["last_action"] = action.model_dump()
        self.local_memory["last_decision_reason"] = decision.reason
        
        return action

    def receive_trophallaxis(self, resource_type: str, amount: float, from_node: str) -> None:
        """Receives resources from a neighbor, updating local pools and triggering homeostasis logs."""
        current = self.resources.get(resource_type, 0.0)
        self.resources[resource_type] = current + amount
        
        # Homeostasis log
        history = self.local_memory.setdefault("trophallaxis_history", [])
        history.append({
            "type": "receive",
            "resource": resource_type,
            "amount": amount,
            "from": from_node
        })
        
        # Strengthen local resilience state
        self.state["resilience"] = self.state.get("resilience", 1.0) + (amount * 0.05)

    def deposit_stigmergy(self, signal: str, intensity: float, edge_id: Optional[str] = None) -> None:
        """Logs/registers stigmergic intent to modify edge weights locally."""
        stigmergy_record = self.local_memory.setdefault("stigmergy_deposits", [])
        stigmergy_record.append({
            "signal": signal,
            "intensity": intensity,
            "edge_id": edge_id
        })

    def compute_local_contribution_to_emergence(self) -> float:
        """Calculates a local metric of alignment.
        
        Evaluates opinion coherence and goal synchronization with the environment.
        """
        # High contribution when opinions are defined and goal-directed
        if not self.opinions:
            return 0.5
        
        # Absolute mean of opinions as cohesion signal
        mean_opinion = sum(abs(v) for v in self.opinions.values()) / len(self.opinions)
        # Factor in resource efficiency
        energy = self.resources.get("energy", 0.0)
        resource_health = min(1.0, energy / 100.0)
        
        return 0.6 * mean_opinion + 0.4 * resource_health

    def decide(self, action_space: List[Action], context: Dict[str, Any]) -> Decision:
        """Executes decision selection. Pluggable override for LLM integration."""
        if self.policy is not None:
            return self.policy(self, action_space, context)
            
        # Default rule-based policy
        return self._default_policy(action_space, context)

    def _default_policy(self, action_space: List[Action], context: Dict[str, Any]) -> Decision:
        """Simple rule-based heuristic for local node state maintenance."""
        neighbors = context.get("neighbors", [])
        local_edges = context.get("local_edges", [])
        energy = self.resources.get("energy", 0.0)
                # === SOTA GOAL PROGRESS UNLOCK (v3.2.1) ===
        active_goals = getattr(self, "goals", []) or context.get("active_goals", [])
        has_complex_goal = any(
            "system design" in str(g).lower() or "analysis" in str(g).lower()
            for g in active_goals
        )
        role = str(self.state.get("role", "")).lower()

        if has_complex_goal:
            # 1. Isolated coordinator → proactively spawn specialist
            if not neighbors and "coordinator" in role:
                return Decision(
                    node_id=str(self.id),
                    selected_action=Action(
                        action_type="spawn_sub_agent",
                        parameters={"role": "system_designer", "skills": ["graph_query", "set_control_mode"]}
                    ),
                    confidence=0.92,
                    reason="Complex goal present + isolated: spawning system_designer sub-agent"
                )

            # 2. Low energy + complex goal → request trophallaxis + emit stigmergic help signal
            if energy < 45.0:
                self.deposit_stigmergy(signal="help_wanted_for_goal", intensity=0.9)
                if neighbors:
                    richest = max(neighbors, key=lambda n: getattr(n, "resources", {}).get("energy", 0) if hasattr(n, "resources") else 0)
                    target_id = str(getattr(richest, "id", richest))
                    return Decision(
                        node_id=str(self.id),
                        selected_action=Action(
                            action_type="trophallaxis_exchange",
                            parameters={"target_node_id": target_id, "resource": "energy", "amount": 12.0}
                        ),
                        confidence=0.88,
                        reason="Low energy + complex goal: requesting trophallaxis and emitting stigmergic help signal"
                    )

            # 3. When delegating complex work, use structured HandoffRequest
            if neighbors:
                try:
                    from graph_swarm_harness.core.handoff_protocol import HandoffRequest, TaskType, HandoffPriority
                    req = HandoffRequest(
                        task_type=TaskType.SYSTEM_DESIGN_ANALYSIS,
                        message="Coordinate and assign system design analysis tasks within the swarm.",
                        details={"analysis_type": "performance", "platform": "HybridControlSwarmGraph"},
                        required_skills=["graph_query", "system_design"],
                        success_criteria=[
                            "Typed HandoffEdge with valid payload_sha256 created",
                            "Provenance delta recorded",
                            "No malformed parameter keys"
                        ],
                        priority=HandoffPriority.HIGH
                    )
                    # The harness agent_loop will convert parameters containing this request
                except Exception:
                    pass  # graceful fallback if harness not in scope
        # Emergency Override (Human Escape Hatch / Homeostatic preservation)
        if energy < 20.0:
            # High priority search for resources
            for action in action_space:
                if action.action_type == "SEARCH_RESOURCE":
                    return Decision(
                        node_id=str(self.id),
                        selected_action=action,
                        confidence=0.95,
                        reason="Energy low (< 20.0), seeking replenishment"
                    )

        # Mode-based routing
        if self.control_mode == ControlMode.HIERARCHICAL:
            # Look for command-type edges and execute command instructions
            commands = context.get("incoming_commands", [])
            if commands:
                command = commands[0] # execute first command
                action = Action(action_type=command.get("type", "IDLE"), parameters=command.get("params", {}))
                return Decision(
                    node_id=str(self.id),
                    selected_action=action,
                    confidence=1.0,
                    reason=f"Hierarchical execution of command: {command.get('type')}"
                )
        
        elif self.control_mode == ControlMode.DECENTRALIZED:
            # Bounded confidence opinion consensus behavior
            for action in action_space:
                if action.action_type == "CONVERGE_OPINION":
                    return Decision(
                        node_id=str(self.id),
                        selected_action=action,
                        confidence=0.8,
                        reason="Executing local opinion alignment"
                    )
                    
        elif self.control_mode == ControlMode.STIGMERGIC:
            # Choose paths/actions with highest virtual pheromone levels on local edges
            if local_edges:
                best_edge = max(local_edges, key=lambda e: e.get("pheromone", 0.0) if isinstance(e, dict) else getattr(e, "weight", 0.0))
                # Target the highest pheromone neighbor
                target = best_edge.target_id if hasattr(best_edge, "target_id") else best_edge.get("target_id")
                if target and target != self.id:
                    action = Action(
                        action_type="SHARE_RESOURCE",
                        parameters={"target_id": target, "amount": 10.0}
                    )
                    return Decision(
                        node_id=str(self.id),
                        selected_action=action,
                        confidence=0.85,
                        reason=f"Stigmergic routing along strong edge to {target}"
                    )
                    
        # Fallback/Emergence default: maintain internal states
        if energy > 80.0 and neighbors:
            # Share energy if abundant
            needy_neighbor = min(neighbors, key=lambda n: n.get("resources", {}).get("energy", 100.0) if isinstance(n, dict) else n.resources.get("energy", 100.0))
            needy_energy = needy_neighbor.get("resources", {}).get("energy", 100.0) if isinstance(needy_neighbor, dict) else needy_neighbor.resources.get("energy", 100.0)
            
            if needy_energy < energy - 20.0:
                neighbor_id = needy_neighbor.get("id") if isinstance(needy_neighbor, dict) else needy_neighbor.id
                return Decision(
                    node_id=str(self.id),
                    selected_action=Action(
                        action_type="SHARE_RESOURCE", 
                        parameters={"target_id": str(neighbor_id), "amount": 10.0}
                    ),
                    confidence=0.7,
                    reason=f"Emergent resource sharing to balance neighbor {neighbor_id}"
                )
                
        return Decision(
            node_id=str(self.id),
            selected_action=Action(action_type="IDLE", parameters={}),
            confidence=0.5,
            reason="No critical local drivers; idling."
        )
