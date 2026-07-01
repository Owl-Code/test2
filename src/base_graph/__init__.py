 """
base_graph
Dynamic Graph Swarm Harness — Foundational Primitives + Phase 1 SOTA Extensions

This package provides the core building blocks for emergent, provenance-rich,
hybrid-controlled swarm systems, now extended with:

- Dynamic 56-skill registry (skill_registry)
- SHA-256 fs-graph checkpointing (fs_graph)
- Emergence-gated MoE expert routing (expert_routing_hybrid)

Posture: HYBRID | ADAPTIVE | trophallaxis_primed | v3.2.1-dev
"""

from __future__ import annotations

__version__ = "3.2.1-dev"
__posture__ = "HYBRID | ADAPTIVE | trophallaxis_primed | v3.2.1+"

# =============================================================================
# Phase 1 SOTA Extensions (new in this evolution)
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

# =============================================================================
# Core Primitives (foundational - to be expanded from existing src/base_graph/core)
# =============================================================================

# Placeholder re-exports for future core modules.
# When core/hybrid_swarm.py, core/provenance.py, etc. are present,
# they will be imported here for a unified top-level API.

# Example future imports (commented until core modules are mirrored/enhanced):
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
]