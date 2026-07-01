"""
base_graph
Dynamic Graph Swarm Harness — Foundational Primitives + Phase 1, 2 & 3 SOTA Extensions

This package provides the core building blocks for emergent, provenance-rich,
hybrid-controlled swarm systems (the Graph Swarm Harness), extended with:

Phase 1:
- Dynamic 56-skill registry
- SHA-256 fs-graph checkpointing
- Emergence-gated MoE expert routing
- Trophallaxis-aware planning handoffs

Phase 2:
- Production factory: create_recommended_swarm(num_agents=512, ...)
- HybridControlSwarmGraph with nodes, health/metrics, and render_dashboard()

Phase 3 (started):
- Minimal textual dashboard rendering

Posture: HYBRID | ADAPTIVE | trophallaxis_primed | v3.2.1-dev
"""

from __future__ import annotations

__version__ = "3.2.1-dev"
__posture__ = "HYBRID | ADAPTIVE | trophallaxis_primed | v3.2.1+"

# =============================================================================
# Core Primitives & Subgraphs
# =============================================================================

from .primitives.node import BaseNode, EmergenceNode
from .primitives.edge import AdaptiveEdge, TrophallaxisEdge
from .primitives.graph import BaseGraph
from .types import ControlMode, EdgeType

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
# Phase 2 - Production Factory & Graph Swarm Harness
# =============================================================================

from .core.hybrid_swarm import HybridControlSwarmGraph

from .factory import (
    SwarmPosture,
    create_recommended_swarm,
    create_recommended_swarm_cli,
)

# =============================================================================
# Phase 3 - Textual Dashboard (observability starter)
# =============================================================================

from .textual_dashboard import (
    render_textual_dashboard,
    print_dashboard,
)

__all__ = [
    # Version & posture
    "__version__",
    "__posture__",

    # Core Primitives & Types
    "BaseNode",
    "EmergenceNode",
    "AdaptiveEdge",
    "TrophallaxisEdge",
    "BaseGraph",
    "ControlMode",
    "EdgeType",

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

    # Production Factory & Graph Swarm Harness (Phase 2)
    "HybridControlSwarmGraph",
    "SwarmPosture",
    "create_recommended_swarm",
    "create_recommended_swarm_cli",

    # Textual Dashboard (Phase 3)
    "render_textual_dashboard",
    "print_dashboard",
]