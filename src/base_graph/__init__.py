 """
base_graph
Dynamic Graph Swarm Harness — Foundational Primitives + Phase 1 & 2 SOTA Extensions

This package provides the core building blocks for emergent, provenance-rich,
hybrid-controlled swarm systems, extended with:

Phase 1:
- Dynamic 56-skill registry (skill_registry)
- SHA-256 fs-graph checkpointing (fs_graph)
- Emergence-gated MoE expert routing (expert_routing_hybrid)
- Trophallaxis-aware planning handoffs (trophallaxis_planner_handoff)

Phase 2 (started):
- Production factory: create_recommended_swarm(num_agents=512, ...)

Posture: HYBRID | ADAPTIVE | trophallaxis_primed | v3.2.1-dev
"""

from __future__ import annotations

__version__ = "3.2.1-dev"
__posture__ = "HYBRID | ADAPTIVE | trophallaxis_primed | v3.2.1+"

# =============================================================================
# Phase 1 SOTA Extensions
# =============================================================================

from .skill_registry import (
    SkillCategory,
    SkillInfo,
    SKILL_REGISTRY,
    list_available_skills,
    get_skill_info,
    register_skill_extension,
    get_skill_registry_summary,
)


from .fs_graph import (
    CheckpointMetadata,
    save_checkpoint,
    load_checkpoint,
    list_checkpoints,
    restore_latest,
    checkpointed_hybrid_step,
)


from .expert_routing_hybrid import (
    EmergenceGatedRouter,
    ExpertScore,
    RoutingDecision,
    create_emergence_gated_router,
    route_experts_for_step,
)


from .trophallaxis_planner_handoff import (
    TrophallaxisPlannerHandoffHook,
    TrophallaxisTransfer,
    HandoffContext,
    create_trophallaxis_handoff_hook,
    resource_aware_plan_handoff,
)

# =============================================================================
# Phase 2 - Production Factory
# =============================================================================

from .factory import (
    HybridControlSwarmGraph,
    SwarmPosture,
    create_recommended_swarm,
    create_recommended_swarm_cli,
)

# =============================================================================
# Core Primitives (foundational - placeholder for future expansion)
# =============================================================================

# Future core imports will go here when src/base_graph/core/ is fully populated:
# from .core.hybrid_swarm import HybridControlSwarmGraph, ControlMode, EmergenceNode
# from .core.provenance import ProvenanceChain
# from .primitives.edge import AdaptiveEdge, TrophallaxisEdge

__all__ = [
    # Version & posture
    "__version__",
    "__posture__",

    # Skill Registry (Phase 1)
    "SkillCategory",
    "SkillInfo",
    "SKILL_REGISTRY",
    "list_available_skills",
    "get_skill_info",
    "register_skill_extension",
    "get_skill_registry_summary",

    # FS Graph / Checkpointing (Phase 1)
    "CheckpointMetadata",
    "save_checkpoint",
    "load_checkpoint",
    "list_checkpoints",
    "restore_latest",
    "checkpointed_hybrid_step",

    # Expert Routing (Phase 1)
    "EmergenceGatedRouter",
    "ExpertScore",
    "RoutingDecision",
    "create_emergence_gated_router",
    "route_experts_for_step",

    # Trophallaxis Handoff (Phase 1)
    "TrophallaxisPlannerHandoffHook",
    "TrophallaxisTransfer",
    "HandoffContext",
    "create_trophallaxis_handoff_hook",
    "resource_aware_plan_handoff",

    # Production Factory (Phase 2)
    "HybridControlSwarmGraph",
    "SwarmPosture",
    "create_recommended_swarm",
    "create_recommended_swarm_cli",
]