 """
factory.py
Production Factory for Recommended Hybrid Control Swarm Harnesses

Part of Phase 2: Production Factory & Scale (SOTA Development Plan v0.1)

Implements the canonical bootstrap function:
    create_recommended_swarm(
        num_agents=512,
        use_fs_graph=True,
        enable_expert_routing=True,
        enable_trophallaxis_handoff=True,
        expose_all_skills=True,
        ...
    ) -> HybridControlSwarmGraph

This factory auto-populates the skill registry, wires Phase 1 modules
(fs_graph checkpointing, EmergenceGatedRouter, TrophallaxisPlannerHandoffHook),
sets the recommended posture, and performs an immediate SHA256 checkpoint.

Designed to be the single entry point for production-grade swarm creation.

Posture: HYBRID | ADAPTIVE | trophallaxis_primed | v3.2.1+
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


from .skill_registry import get_skill_registry_summary, list_available_skills

from .fs_graph import save_checkpoint, checkpointed_hybrid_step

from .expert_routing_hybrid import create_emergence_gated_router, RoutingDecision

from .trophallaxis_planner_handoff import create_trophallaxis_handoff_hook, TrophallaxisTransfer


@dataclass
class SwarmPosture:
    """Live posture metadata for a recommended swarm."""
    mode: str = "HYBRID"
    adaptive: bool = True
    trophallaxis_primed: bool = True
    emergence_target: float = 0.92
    value_alignment_score: float = 0.92
    homeostasis: str = "high"
    fs_graph_active: bool = True
    expert_routing_active: bool = True
    version: str = "3.2.1-dev"


@dataclass
class EmergenceNode:
    """Lightweight placeholder node for the recommended swarm."""
    id: str
    opinions: Dict[str, float] = field(default_factory=dict)
    health: float = 0.9
    role: str = "generalist"


class HybridControlSwarmGraph:
    """
    Production-grade HybridControlSwarmGraph with Phase 1 & 2 capabilities wired in.

    This is a functional skeleton that can be extended with the full core primitives
    (EmergenceNode, AdaptiveEdge, ProvenanceChain, etc.) later.
    """

    def __init__(self, name: str = "recommended-swarm", num_agents: int = 512):
        self.name = name
        self.num_agents_target = num_agents
        self.control_mode = "HYBRID"
        self.emergence_level = 0.65
        self.posture = SwarmPosture()
        self._checkpoint_sha: Optional[str] = None

        # Phase 1 modules wired
        self._router = create_emergence_gated_router(k=3, emergence_target=0.92)
        self._trophallaxis_hook = create_trophallaxis_handoff_hook(efficiency_base=0.87)
        self._skill_summary = get_skill_registry_summary()

        # Lightweight internal graph
        self.nodes: Dict[str, EmergenceNode] = {}
        self.edges: List[Dict[str, str]] = []
        self._initialize_minimal_graph(min(32, max(8, num_agents // 16)))

    def _initialize_minimal_graph(self, node_count: int) -> None:
        """Create a small set of placeholder nodes for bootstrap."""
        for i in range(node_count):
            node_id = f"node_{i:03d}"
            self.nodes[node_id] = EmergenceNode(
                id=node_id,
                opinions={"main": 0.1 * (i % 5 - 2)},
                health=0.85 + 0.1 * (i % 3),
                role="generalist" if i % 3 != 0 else "specialist",
            )
        # Create a few simple edges
        node_ids = list(self.nodes.keys())
        for i in range(min(len(node_ids) - 1, 12)):
            self.edges.append({"source": node_ids[i], "target": node_ids[i + 1]})

    def hybrid_step(self, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Run one hybrid control step with expert routing + auto-checkpointing."""
        context = context or {"emergence_level": self.emergence_level, "task_complexity": 0.7}

        # Sparse expert routing (Phase 1)
        decision: RoutingDecision = self._router.route(
            list(self._skill_summary.get("by_category", {}).keys())[:10],
            context=context,
        )

        # Simulate emergence growth (stronger under hybrid mode)
        growth = 0.018 if self.control_mode == "HYBRID" else 0.012
        self.emergence_level = min(0.99, self.emergence_level + growth)

        result = {
            "step": "hybrid_step",
            "mode": self.control_mode,
            "emergence": round(self.emergence_level, 3),
            "experts_activated": decision.selected_experts,
            "active_nodes": len(self.nodes),
        }

        # Auto-checkpoint via fs_graph (Phase 1)
        checkpointed_hybrid_step(self, lambda s: result, auto_save=True)

        return result

    def set_control_mode(self, mode: str) -> None:
        """Switch control regime."""
        self.control_mode = mode
        self.posture.mode = mode

    def get_posture(self) -> SwarmPosture:
        self.posture.emergence_target = round(self.emergence_level, 2)
        return self.posture

    def add_node(self, node_id: str, **kwargs) -> EmergenceNode:
        """Add a new node to the swarm."""
        node = EmergenceNode(id=node_id, **kwargs)
        self.nodes[node_id] = node
        return node

    def checkpoint(self, name: Optional[str] = None) -> str:
        """Manual SHA256 checkpoint of current swarm state."""
        state = {
            "name": self.name,
            "control_mode": self.control_mode,
            "emergence_level": self.emergence_level,
            "posture": self.posture.__dict__,
            "node_count": len(self.nodes),
            "edge_count": len(self.edges),
            "skill_summary": self._skill_summary,
        }
        sha, _ = save_checkpoint(state, name=name or f"{self.name}_manual")
        self._checkpoint_sha = sha
        return sha


def create_recommended_swarm(
    num_agents: int = 512,
    use_fs_graph: bool = True,
    enable_expert_routing: bool = True,
    enable_trophallaxis_handoff: bool = True,
    expose_all_skills: bool = True,
    name: str = "recommended-swarm",
) -> HybridControlSwarmGraph:
    """
    Recommended production bootstrap for Hybrid Control Swarm Harnesses (v3.2.1+).

    This is the canonical factory. It wires all Phase 1 capabilities and returns
    a ready-to-use HybridControlSwarmGraph with the full recommended posture.
    """
    swarm = HybridControlSwarmGraph(name=name, num_agents=num_agents)

    if expose_all_skills:
        swarm._skill_summary = get_skill_registry_summary()

    if enable_expert_routing:
        swarm._router = create_emergence_gated_router(
            k=min(5, max(2, num_agents // 100)),
            emergence_target=0.92,
        )

    if enable_trophallaxis_handoff:
        swarm._trophallaxis_hook = create_trophallaxis_handoff_hook(efficiency_base=0.87)

    # Set full recommended posture
    swarm.posture = SwarmPosture(
        mode="HYBRID",
        adaptive=True,
        trophallaxis_primed=True,
        emergence_target=0.92,
        value_alignment_score=0.92,
        homeostasis="high",
        fs_graph_active=use_fs_graph,
        expert_routing_active=enable_expert_routing,
        version="3.2.1-dev",
    )

    # Immediate bootstrap checkpoint
    if use_fs_graph:
        state = {
            "name": name,
            "num_agents_target": num_agents,
            "posture": swarm.posture.__dict__,
            "initial_node_count": len(swarm.nodes),
            "bootstrap_complete": True,
            "skill_count": swarm._skill_summary.get("total_skills", 0),
        }
        sha, _ = save_checkpoint(state, name=f"{name}_bootstrap")
        swarm._checkpoint_sha = sha

    return swarm


# CLI entry point (registered in pyproject.toml as base-graph-bootstrap)

def create_recommended_swarm_cli():
    """CLI wrapper for the `base-graph-bootstrap` console script."""
    import argparse

    parser = argparse.ArgumentParser(description="Bootstrap a recommended Hybrid Control Swarm")
    parser.add_argument("--agents", type=int, default=512, help="Target number of agents")
    parser.add_argument("--name", type=str, default="cli-swarm", help="Swarm name")
    args = parser.parse_args()

    swarm = create_recommended_swarm(num_agents=args.agents, name=args.name)
    print(f"Created recommended swarm: {swarm.name}")
    print(f"Target agents: {swarm.num_agents_target}")
    print(f"Initial nodes: {len(swarm.nodes)}")
    print(f"Posture: {swarm.get_posture().__dict__}")
    print(f"Bootstrap checkpoint: {swarm._checkpoint_sha}")
    return swarm


if __name__ == "__main__":
    swarm = create_recommended_swarm(num_agents=64, name="demo-factory-swarm")
    print("Factory bootstrap complete.")
    print("Posture:", swarm.get_posture().__dict__)
    result = swarm.hybrid_step({"task_complexity": 0.9})
    print("First hybrid_step result:", result)
    print("Active nodes:", len(swarm.nodes))