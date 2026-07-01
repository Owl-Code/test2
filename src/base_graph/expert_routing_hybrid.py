 """
expert_routing_hybrid.py
MoE-inspired Expert Routing with Emergence-Gated Top-k Selection

Part of Phase 1: Core Hardening & Full Skill Exposure (SOTA Development Plan v0.1)

Implements sparse activation and dynamic specialization inside HybridControlSwarmGraph:
- Emergence-gated expert selection (top-k based on local emergence signals, node health, skill affinity)
- Per-node "extended thinking" via lightweight internal diffusion
- Integration with skill_registry for dynamic expert discovery
- Designed to work with expert-routing-hybrid posture without requiring full swarm activation every step

This module enables o1-style deeper deliberation on complex tasks while preserving
emergence, stigmergy, and hybrid control.

Posture: HYBRID | ADAPTIVE | trophallaxis_primed | v3.2.1+
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple


from .skill_registry import (
    SKILL_REGISTRY,
    SkillCategory,
    get_skill_info,
    list_available_skills,
)


@dataclass
class ExpertScore:
    """Score for an expert (node or skill) during routing."""
    expert_id: str
    score: float
    reason: str
    emergence_signal: float = 0.0
    skill_affinity: float = 0.0


@dataclass
class RoutingDecision:
    """Result of expert routing."""
    selected_experts: List[str]
    scores: List[ExpertScore]
    mode: str = "emergence_gated_top_k"
    k: int = 3
    rationale: str = ""


class EmergenceGatedRouter:
    """
    MoE-style router that selects a small number of experts (nodes or skills)
    based on emergence signals rather than always activating the full swarm.
    """

    def __init__(
        self,
        k: int = 3,
        emergence_threshold: float = 0.6,
        use_skill_registry: bool = True,
    ):
        self.k = k
        self.emergence_threshold = emergence_threshold
        self.use_skill_registry = use_skill_registry
        self._last_decision: Optional[RoutingDecision] = None

    def score_expert(
        self,
        expert_id: str,
        context: Dict[str, Any],
        node_state: Optional[Dict[str, Any]] = None,
    ) -> ExpertScore:
        """
        Score a single expert (node or skill) for the current context.
        Higher score = more relevant for current emergence needs.
        """
        emergence = context.get("emergence_level", 0.5)
        task_complexity = context.get("task_complexity", 0.5)
        node_health = (node_state or {}).get("health", 0.8)

        # Base emergence-gated score
        emergence_signal = max(0.0, emergence - self.emergence_threshold)

        # Skill affinity (if using registry)
        skill_affinity = 0.0
        if self.use_skill_registry:
            skill_info = get_skill_info(expert_id)
            if skill_info:
                # Boost score for advanced reasoning / orchestration skills on complex tasks
                if skill_info.category in (
                    SkillCategory.ADVANCED_REASONING,
                    SkillCategory.GRAPH_SWARM_ORCHESTRATION,
                ):
                    skill_affinity = 0.3 * task_complexity

        # Composite score (can be extended with learned weights later)
        score = (
            0.5 * emergence_signal +
            0.3 * skill_affinity +
            0.2 * node_health
        )

        reason = f"emergence={emergence:.2f}, affinity={skill_affinity:.2f}, health={node_health:.2f}"

        return ExpertScore(
            expert_id=expert_id,
            score=score,
            reason=reason,
            emergence_signal=emergence_signal,
            skill_affinity=skill_affinity,
        )

    def route(
        self,
        candidate_experts: List[str],
        context: Dict[str, Any],
        node_states: Optional[Dict[str, Dict[str, Any]]] = None,
    ) -> RoutingDecision:
        """
        Select top-k experts using emergence-gated scoring.
        """
        node_states = node_states or {}
        scored: List[ExpertScore] = []

        for expert_id in candidate_experts:
            node_state = node_states.get(expert_id)
            scored.append(self.score_expert(expert_id, context, node_state))

        # Sort by score descending and take top-k
        scored.sort(key=lambda x: x.score, reverse=True)
        selected = scored[: self.k]

        rationale = (
            f"Selected top-{self.k} from {len(candidate_experts)} candidates "
            f"using emergence threshold {self.emergence_threshold}"
        )

        decision = RoutingDecision(
            selected_experts=[s.expert_id for s in selected],
            scores=selected,
            k=self.k,
            rationale=rationale,
        )
        self._last_decision = decision
        return decision

    def get_extended_thinking_prompt(
        self,
        expert_id: str,
        base_prompt: str,
        context: Dict[str, Any],
    ) -> str:
        """
        Generate an "extended thinking" prompt for a selected expert.
        In a full implementation this could trigger internal diffusion steps
        or call a heavier reasoning path for that expert only.
        """
        emergence = context.get("emergence_level", 0.5)
        return (
            f"[Extended Thinking Mode | expert={expert_id} | emergence={emergence:.2f}]\n"
            f"{base_prompt}\n"
            "Consider long-horizon implications, cross-skill synergies, and "
            "potential second-order effects before responding."
        )

    def get_last_decision(self) -> Optional[RoutingDecision]:
        return self._last_decision


# =============================================================================
# CONVENIENCE FACTORY
# =============================================================================

def create_emergence_gated_router(
    k: int = 3,
    emergence_target: float = 0.92,
) -> EmergenceGatedRouter:
    """Factory aligned with create_recommended_swarm posture."""
    return EmergenceGatedRouter(
        k=k,
        emergence_threshold=max(0.3, emergence_target - 0.3),
    )


# =============================================================================
# INTEGRATION STUB (for future HybridControlSwarmGraph wiring)
# =============================================================================

def route_experts_for_step(
    swarm: Any,
    context: Optional[Dict[str, Any]] = None,
) -> RoutingDecision:
    """
    High-level integration point.
    Future: called inside hybrid_step() to sparsely activate only relevant experts.
    """
    router = create_emergence_gated_router()
    context = context or {"emergence_level": getattr(swarm, "emergence_level", 0.7)}

    # In real usage we would pull live node/skill IDs from the swarm + registry
    candidates = list(SKILL_REGISTRY.keys())[:12]  # demo slice

    return router.route(candidates, context)


if __name__ == "__main__":
    print("expert_routing_hybrid v3.2.1-dev — Emergence-Gated MoE Router")
    router = create_emergence_gated_router(k=3)
    decision = router.route(
        ["base-graph", "diffusion-graph", "meta-skill-evolver", "planner-graph", "philosophy"],
        {"emergence_level": 0.85, "task_complexity": 0.9},
    )
    print("Selected experts:", decision.selected_experts)
    print("Rationale:", decision.rationale)