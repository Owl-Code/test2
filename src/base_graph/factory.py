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
from typing import Any, Dict, Optional


from .skill_registry import get_skill_registry_summary, list_available_skills

from .fs_graph import save_checkpoint, checkpointed_hybrid_step

from .expert_routing_hybrid import create_emergence_gated_router

from .trophallaxis_planner_handoff import create_trophallaxis_handoff_hook


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


class HybridControlSwarmGraph:
    """
    Minimal production-grade HybridControlSwarmGraph skeleton.

    In a full implementation this would inherit from or compose the core
    primitives (EmergenceNode, AdaptiveEdge, ProvenanceChain, etc.).
    For Phase 2 bootstrap we provide a functional shell that wires the new
    Phase 1 capabilities.
    """

    def __init__(self, name: str = "recommended-swarm"):
        self.name = name
        self.control_mode = "HYBRID"
        self.emergence_level = 0.0
        self.posture = SwarmPosture()
        self._checkpoint_sha: Optional[str] = None
        self._router = create_emergence_gated_router(k=3, emergence_target=0.92)
        self._trophallaxis_hook = create_trophallaxis_handoff_hook()
        self._skill_summary = get_skill_registry_summary()

    def hybrid_step(self, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Run one hybrid control step with optional expert routing and checkpointing."""
        context = context or {"emergence_level": self.emergence_level}

        # Sparse expert routing (Phase 1)
        decision = self._router.route(
            list(self._skill_summary.get("by_category", {}).keys())[:8],
            context=context,
        )

        # Simulate emergence growth
        self.emergence_level = min(0.99, self.emergence_level + 0.015)

        result = {
            "step": "hybrid_step",
            "mode": self.control_mode,
            "emergence": round(self.emergence_level, 3),
            "experts_activated": decision.selected_experts,
        }

        # Auto-checkpoint via fs_graph wrapper (Phase 1)
        checkpointed_hybrid_step(self, lambda s: result, auto_save=True)

        return result

    def set_control_mode(self, mode: str) -> None:
        """Switch between HYBRID, DECENTRALIZED, HIERARCHICAL, etc."""
        self.control_mode = mode
        self.posture.mode = mode

    def get_posture(self) -> SwarmPosture:
        self.posture.emergence_target = round(self.emergence_level, 2)
        return self.posture

    def checkpoint(self, name: Optional[str] = None) -> str:
        """Manual SHA256 checkpoint of current swarm state."""
        state = {
            "name": self.name,
            "control_mode": self.control_mode,
            "emergence_level": self.emergence_level,
            "posture": self.posture.__dict__,
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
    Recommended production bootstrap for Hybrid Control Swarm Harnesses.

    This is the canonical factory for creating swarms with the full v3.2.1+
    posture and all Phase 1 capabilities pre-wired.

    Args:
        num_agents: Target scale (used for future large-graph optimizations).
        use_fs_graph: Enable automatic SHA256 checkpointing.
        enable_expert_routing: Enable EmergenceGatedRouter (sparse activation).
        enable_trophallaxis_handoff: Enable resource-aware handoff hook.
        expose_all_skills: Populate and expose the full 56-skill registry.
        name: Human-readable swarm identifier.

    Returns:
        A fully configured HybridControlSwarmGraph instance.
    """
    swarm = HybridControlSwarmGraph(name=name)

    # Wire Phase 1 capabilities
    if expose_all_skills:
        swarm._skill_summary = get_skill_registry_summary()

    if enable_expert_routing:
        swarm._router = create_emergence_gated_router(
            k=min(5, max(2, num_agents // 100)),
            emergence_target=0.92,
        )

    if enable_trophallaxis_handoff:
        swarm._trophallaxis_hook = create_trophallaxis_handoff_hook(efficiency_base=0.87)

    # Initial posture sync
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

    # Immediate bootstrap checkpoint (fs_graph)
    if use_fs_graph:
        state = {
            "name": name,
            "num_agents_target": num_agents,
            "posture": swarm.posture.__dict__,
            "skill_count": swarm._skill_summary.get("total_skills", 0),
            "bootstrap_complete": True,
        }
        sha, _ = save_checkpoint(state, name=f"{name}_bootstrap")
        swarm._checkpoint_sha = sha

    return swarm


# CLI entry point (registered in pyproject.toml)

def create_recommended_swarm_cli():
    """CLI wrapper for `base-graph-bootstrap` entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Bootstrap a recommended Hybrid Control Swarm")
    parser.add_argument("--agents", type=int, default=512, help="Target number of agents")
    parser.add_argument("--name", type=str, default="cli-swarm", help="Swarm name")
    args = parser.parse_args()

    swarm = create_recommended_swarm(num_agents=args.agents, name=args.name)
    print(f"Created recommended swarm: {swarm.name}")
    print(f"Posture: {swarm.get_posture().__dict__}")
    print(f"Initial checkpoint: {swarm._checkpoint_sha}")
    return swarm


if __name__ == "__main__":
    swarm = create_recommended_swarm(num_agents=128, name="demo-factory-swarm")
    print("Factory bootstrap complete.")
    print("Posture:", swarm.get_posture().__dict__)
    result = swarm.hybrid_step({"task_complexity": 0.9})
    print("First hybrid_step result:", result)