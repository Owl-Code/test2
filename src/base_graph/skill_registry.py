 """
skill_registry.py
Dynamic Skill Registry for the Hybrid Control Swarm Harness (base_graph)

Part of Phase 1: Core Hardening & Full Skill Exposure (SOTA Development Plan v0.1)

Exposes the complete catalog of 56 skills across 9 categories.
Supports dynamic registration of extensions and queryable access for
HybridControlSwarmGraph, expert routing, meta-skill-evolver, and MCP layers.

This module realizes the "Extensibility Hooks" requirement from the original
README while enabling the full 56-skill production posture.

Posture: HYBRID | ADAPTIVE | trophallaxis_primed | v3.2.1+
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class SkillCategory(str, Enum):
    """Nine primary categories for the 56-skill ecosystem."""
    GRAPH_SWARM_ORCHESTRATION = "Graph & Swarm Orchestration"
    PERSISTENCE_MEMORY = "Persistence & Memory"
    OBSERVABILITY_REPORTING = "Observability & Reporting"
    PLANNING_COORDINATION = "Planning & Coordination"
    ADVANCED_REASONING = "Advanced Reasoning (Tagged)"
    SIMULATION_EVOLUTION = "Simulation & Evolution"
    LANGUAGE_WRITING = "Language & Writing"
    DOMAIN_MEDIA = "Domain & Media"
    PHYSICS_MECHANICAL = "Physics & Mechanical"


@dataclass
class SkillInfo:
    """Structured metadata for a registered skill."""
    name: str
    category: SkillCategory
    description: str
    status: str = "core"          # core | planned | live | extension
    module_path: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    version_introduced: str = "3.2.1-dev"


# =============================================================================
# MASTER SKILL REGISTRY (56 skills - dynamically extensible)
# =============================================================================

SKILL_REGISTRY: Dict[str, SkillInfo] = {
    # --- Graph & Swarm Orchestration (11) ---
    "base-graph": SkillInfo(
        name="base-graph",
        category=SkillCategory.GRAPH_SWARM_ORCHESTRATION,
        description="Foundational primitives: EmergenceNode, AdaptiveEdge, HybridControlSwarmGraph, ProvenanceChain (SHA-256).",
        status="core",
        module_path="src.base_graph.core",
        tags=["emergence", "stigmergy", "trophallaxis"],
    ),
    "hierarchical-graph": SkillInfo(
        name="hierarchical-graph",
        category=SkillCategory.GRAPH_SWARM_ORCHESTRATION,
        description="Multi-level organization, command hierarchies, tree/DAG structures, roll-up of collective states.",
        status="core",
        tags=["hierarchy", "multi-scale"],
    ),
    "diffusion-graph": SkillInfo(
        name="diffusion-graph",
        category=SkillCategory.GRAPH_SWARM_ORCHESTRATION,
        description="Advanced diffusion models (SIR/SIS, opinion dynamics, reaction-diffusion, threshold models).",
        status="core",
        tags=["diffusion", "opinion-dynamics"],
    ),
    "hybrid-control-swarm": SkillInfo(
        name="hybrid-control-swarm",
        category=SkillCategory.GRAPH_SWARM_ORCHESTRATION,
        description="Integrative crown layer balancing hierarchical direction with decentralized emergence, diffusion, stigmergy and trophallaxis.",
        status="core",
        tags=["hybrid", "control", "emergence"],
    ),
    "organizational-swarm": SkillInfo(
        name="organizational-swarm",
        category=SkillCategory.GRAPH_SWARM_ORCHESTRATION,
        description="Structured multi-level swarms combining explicit hierarchy with rich diffusion processes.",
        status="core",
        tags=["organization", "division-of-labor"],
    ),
    "decentralized-swarm-coordinator": SkillInfo(
        name="decentralized-swarm-coordinator",
        category=SkillCategory.GRAPH_SWARM_ORCHESTRATION,
        description="Decentralized consensus, emergent coordinator selection, stigmergic coordination via diffusion.",
        status="core",
        tags=["decentralized", "consensus"],
    ),
    "expert-routing-hybrid": SkillInfo(
        name="expert-routing-hybrid",
        category=SkillCategory.GRAPH_SWARM_ORCHESTRATION,
        description="MoE-inspired expert routing with emergence-gated top-k coordinator selection and per-node extended thinking.",
        status="planned",  # Phase 1 target
        tags=["moe", "routing", "expert"],
    ),
    "stateful-hybrid-control": SkillInfo(
        name="stateful-hybrid-control",
        category=SkillCategory.GRAPH_SWARM_ORCHESTRATION,
        description="LangGraph-style stateful primitives, first-class tool calling, robust checkpointing with time-travel.",
        status="planned",
        tags=["stateful", "checkpoint"],
    ),
    "handoff-protocol-enhancer": SkillInfo(
        name="handoff-protocol-enhancer",
        category=SkillCategory.GRAPH_SWARM_ORCHESTRATION,
        description="Graph-native, safe, observable, reversible handoff protocols for hybrid control mode switches and coordinator changes.",
        status="live",  # Recent v3.2.1 addition
        tags=["handoff", "reversible"],
    ),
    "adaptive-swarm-patterns-graph": SkillInfo(
        name="adaptive-swarm-patterns-graph",
        category=SkillCategory.GRAPH_SWARM_ORCHESTRATION,
        description="Library of reusable hybrid control patterns (Mission Command, Stigmergic Foraging, Holacracy-inspired, Research Collective, etc.).",
        status="core",
        tags=["patterns", "playbooks"],
    ),
    "trophallaxis-planner-handoff-hook": SkillInfo(
        name="trophallaxis-planner-handoff-hook",
        category=SkillCategory.GRAPH_SWARM_ORCHESTRATION,
        description="Cross-skill hook enabling bidirectional trophallaxis-aware resource exchange during hierarchical planning handoffs.",
        status="live",
        tags=["trophallaxis", "resource-aware"],
    ),

    # --- Persistence & Memory (3) ---
    "fs-graph": SkillInfo(
        name="fs-graph",
        category=SkillCategory.PERSISTENCE_MEMORY,
        description="File System Graph for persistent state (control mode, nodes, metrics, plans, handoff history). SHA256 checkpoints to artifacts/.",
        status="planned",  # Phase 1 target
        tags=["persistence", "sha256", "checkpoint"],
    ),
    "memory-provenance-mcp": SkillInfo(
        name="memory-provenance-mcp",
        category=SkillCategory.PERSISTENCE_MEMORY,
        description="Layered vector + graph RAG, episodic and semantic memory with full provenance tracking and extended Model Context Protocol.",
        status="planned",
        tags=["memory", "mcp", "provenance"],
    ),
    "mcp-graph": SkillInfo(
        name="mcp-graph",
        category=SkillCategory.PERSISTENCE_MEMORY,
        description="Multi-Context Planner Graph managing multiple simultaneous planning contexts, goals, and time horizons.",
        status="planned",
        tags=["mcp", "multi-context"],
    ),

    # --- Observability & Reporting (5) ---
    "observability-graph": SkillInfo(
        name="observability-graph",
        category=SkillCategory.OBSERVABILITY_REPORTING,
        description="Graph-native observability, tracing, snapshots, health dashboards for hybrid-control swarms. Deep visibility into control modes and emergence.",
        status="planned",
        tags=["observability", "tracing"],
    ),
    "obs-metrics-long-horizon-graph": SkillInfo(
        name="obs-metrics-long-horizon-graph",
        category=SkillCategory.OBSERVABILITY_REPORTING,
        description="Long-horizon metrics, stability analysis, trend detection, anomaly identification, health scoring from observability-graph.",
        status="planned",
        tags=["metrics", "long-horizon"],
    ),
    "dashboard-graph": SkillInfo(
        name="dashboard-graph",
        category=SkillCategory.OBSERVABILITY_REPORTING,
        description="Visualization and dashboard generation. Rich textual + matplotlib plots, actionable visual summaries, narrative insight cards. Auto-refresh for >=64 nodes.",
        status="planned",
        tags=["dashboard", "visualization"],
    ),
    "reporting-graph": SkillInfo(
        name="reporting-graph",
        category=SkillCategory.OBSERVABILITY_REPORTING,
        description="Professional reporting layer bridging swarm intelligence with document generation (docx, pdf, pptx, xlsx).",
        status="planned",
        tags=["reporting", "documents"],
    ),
    "statistics-graph": SkillInfo(
        name="statistics-graph",
        category=SkillCategory.OBSERVABILITY_REPORTING,
        description="Advanced statistical and causal analysis: correlation, regression, anomaly detection, risk scoring, emergence stability on long-horizon metrics.",
        status="planned",
        tags=["statistics", "causal"],
    ),

    # --- Planning & Coordination (4) ---
    "planner-graph": SkillInfo(
        name="planner-graph",
        category=SkillCategory.PLANNING_COORDINATION,
        description="Graph-native planner for hybrid-control swarms. Hierarchical plan decomposition, mode-aware planning, reversible handoff steps, provenance-aware execution tracking.",
        status="planned",
        tags=["planner", "decomposition"],
    ),
    "multi-scale-context-bridge": SkillInfo(
        name="multi-scale-context-bridge",
        category=SkillCategory.PLANNING_COORDINATION,
        description="Strategic propagation of goals, intent, and context coherently across organizational levels, time scales, and functional clusters.",
        status="planned",
        tags=["multi-scale", "context"],
    ),
    "nl-command-translator": SkillInfo(
        name="nl-command-translator",
        category=SkillCategory.PLANNING_COORDINATION,
        description="Robust natural language to precise HybridControlSwarmGraph API translator with confidence scoring and trade-off surfacing.",
        status="planned",
        tags=["nl", "translator"],
    ),

    # --- Advanced Reasoning (4) ---
    "philosophy": SkillInfo(
        name="philosophy",
        category=SkillCategory.ADVANCED_REASONING,
        description="Philosophical analysis, logical reasoning, aesthetic judgment, ethical deliberation, conceptual clarification for AI/swarm systems and eudaimonia.",
        status="core",
        tags=["philosophy", "ethics", "eudaimonia"],
    ),
    "trophallaxis-graph-skill": SkillInfo(
        name="trophallaxis-graph-skill",
        category=SkillCategory.ADVANCED_REASONING,
        description="Bio-inspired trophallaxis (resource, energy, information, token exchange) between nodes. Enhances emergence and antifragility.",
        status="core",
        tags=["trophallaxis", "resource-exchange"],
    ),
    "mathematician-and-modeling-mathematics-graph-skill": SkillInfo(
        name="mathematician-and-modeling-mathematics-graph-skill",
        category=SkillCategory.ADVANCED_REASONING,
        description="Rigorous mathematical modeling, symbolic/numeric analysis, optimization, differential equations, spectral methods, graph Laplacians.",
        status="core",
        tags=["math", "modeling", "spectral"],
    ),
    "graph-theory-linear-algebra-and-topology-graph-skill": SkillInfo(
        name="graph-theory-linear-algebra-and-topology-graph-skill",
        category=SkillCategory.ADVANCED_REASONING,
        description="Advanced graph-theoretic analysis via linear algebra (spectral methods, Laplacians, eigenvalues) and topology (persistent homology, Betti numbers).",
        status="core",
        tags=["graph-theory", "topology", "persistent-homology"],
    ),
    "constitutional-ethical-alignment": SkillInfo(
        name="constitutional-ethical-alignment",
        category=SkillCategory.ADVANCED_REASONING,
        description="Constitutional critique (Anthropic-style), value alignment metrics, diffusion-based ethical consensus mechanisms into HybridControlSwarmGraph.",
        status="planned",
        tags=["alignment", "constitutional", "ethics"],
    ),

    # --- Simulation & Evolution (2) ---
    "simulation-harness-graph": SkillInfo(
        name="simulation-harness-graph",
        category=SkillCategory.SIMULATION_EVOLUTION,
        description="Standardized simulation, benchmarking, and scientific validation framework. Reproducible experiments, statistical comparison, automated reporting.",
        status="planned",
        tags=["simulation", "benchmarking", "validation"],
    ),
    "meta-skill-evolver": SkillInfo(
        name="meta-skill-evolver",
        category=SkillCategory.SIMULATION_EVOLUTION,
        description="Self-improvement engine. Analyzes health, emergence patterns, decision quality; proposes new skills; validates via simulation-harness; integrates via reversible handoffs.",
        status="planned",
        tags=["meta", "self-improvement", "evolution"],
    ),

    # --- Language & Writing (3) ---
    "language-graph": SkillInfo(
        name="language-graph",
        category=SkillCategory.LANGUAGE_WRITING,
        description="Structured language generation and understanding grounded in swarm state (emergence, control mode, opinions, metrics, provenance).",
        status="core",
        tags=["language", "explainability"],
    ),
    "writing-graph": SkillInfo(
        name="writing-graph",
        category=SkillCategory.LANGUAGE_WRITING,
        description="High-quality report, plan, narrative, and stakeholder communication generation from swarm data. Supports Markdown + DOCX/PDF conversion.",
        status="planned",
        tags=["writing", "reporting"],
    ),

    # --- Domain & Media (6) ---
    "docx": SkillInfo(
        name="docx",
        category=SkillCategory.DOMAIN_MEDIA,
        description="Create, read, edit Word documents (.docx). Professional formatting, tables of contents, tracked changes, image insertion.",
        status="core",
        tags=["document", "docx"],
    ),
    "pdf": SkillInfo(
        name="pdf",
        category=SkillCategory.DOMAIN_MEDIA,
        description="Full PDF lifecycle: reading, merging, splitting, watermarks, forms, encryption, OCR, image extraction.",
        status="core",
        tags=["pdf", "ocr"],
    ),
    "pptx": SkillInfo(
        name="pptx",
        category=SkillCategory.DOMAIN_MEDIA,
        description="Create and manipulate PowerPoint presentations. Slides, layouts, speaker notes, charts, templates.",
        status="core",
        tags=["pptx", "presentation"],
    ),
    "xlsx": SkillInfo(
        name="xlsx",
        category=SkillCategory.DOMAIN_MEDIA,
        description="Spreadsheet creation, reading, editing, formulas, charting, data cleaning, restructuring for .xlsx/.xlsm/.csv.",
        status="core",
        tags=["xlsx", "spreadsheet"],
    ),
    "ffmpeg": SkillInfo(
        name="ffmpeg",
        category=SkillCategory.DOMAIN_MEDIA,
        description="Media processing: inspect, convert, trim, resize, compress, extract frames/audio, subtitles, GIFs, storyboards, video analysis.",
        status="core",
        tags=["media", "video", "audio"],
    ),
    "web-protocol-graph": SkillInfo(
        name="web-protocol-graph",
        category=SkillCategory.DOMAIN_MEDIA,
        description="Advanced web research, protocol-aware crawling, robust data extraction from HTML/JS/CSS, deep OSI model understanding.",
        status="planned",
        tags=["web", "crawling", "protocol"],
    ),

    # --- Physics & Mechanical (3) ---
    "physics-graph-skill": SkillInfo(
        name="physics-graph-skill",
        category=SkillCategory.PHYSICS_MECHANICAL,
        description="Particle dynamics, forces, energy conservation, kinematics, constraints, field simulations in HybridControlSwarmGraph.",
        status="core",
        tags=["physics", "simulation"],
    ),
    "mechanical-engineering-graph-skill": SkillInfo(
        name="mechanical-engineering-graph-skill",
        category=SkillCategory.PHYSICS_MECHANICAL,
        description="Mechanism design, kinematics, dynamics of linkages, structural analysis, actuator modeling, constraint satisfaction.",
        status="core",
        tags=["mechanical", "kinematics"],
    ),
    "rrt-star-graph-skill": SkillInfo(
        name="rrt-star-graph-skill",
        category=SkillCategory.PHYSICS_MECHANICAL,
        description="Sampling-based optimal path and motion planning (RRT*) on continuous or hybrid configuration spaces.",
        status="core",
        tags=["path-planning", "rrt*"],
    ),
    "trigonometry-and-geometry-graph-skill": SkillInfo(
        name="trigonometry-and-geometry-graph-skill",
        category=SkillCategory.PHYSICS_MECHANICAL,
        description="Spatial primitives, vector math, distance/angle computations, transformations, convex/concave tests, Euclidean embeddings.",
        status="core",
        tags=["geometry", "trigonometry"],
    ),
}


# =============================================================================
# PUBLIC API
# =============================================================================

def list_available_skills(
    category: Optional[SkillCategory] = None,
    status: Optional[str] = None,
) -> List[SkillInfo]:
    """Return filtered list of skills. Supports category and status filtering."""
    skills = list(SKILL_REGISTRY.values())
    if category:
        skills = [s for s in skills if s.category == category]
    if status:
        skills = [s for s in skills if s.status == status]
    return skills


def get_skill_info(name: str) -> Optional[SkillInfo]:
    """Retrieve full SkillInfo for a given skill name (case-insensitive)."""
    key = name.lower()
    for skill_name, info in SKILL_REGISTRY.items():
        if skill_name.lower() == key:
            return info
    return None


def register_skill_extension(
    name: str,
    description: str,
    category: SkillCategory = SkillCategory.GRAPH_SWARM_ORCHESTRATION,
    tags: Optional[List[str]] = None,
) -> SkillInfo:
    """
    Register a new custom skill extension at runtime.
    Used by HybridControlSwarmGraph.register_skill_extension() and downstream MCP layers.
    """
    if name in SKILL_REGISTRY:
        raise ValueError(f"Skill '{name}' already exists. Use update or different name.")

    info = SkillInfo(
        name=name,
        category=category,
        description=description,
        status="extension",
        tags=tags or [],
        version_introduced="3.2.1-dev",
    )
    SKILL_REGISTRY[name] = info
    return info


def get_skill_registry_summary() -> Dict[str, Any]:
    """Return summary statistics and categorized breakdown for dashboards / health reports."""
    total = len(SKILL_REGISTRY)
    by_category: Dict[str, int] = {}
    by_status: Dict[str, int] = {}

    for info in SKILL_REGISTRY.values():
        by_category[info.category.value] = by_category.get(info.category.value, 0) + 1
        by_status[info.status] = by_status.get(info.status, 0) + 1

    return {
        "total_skills": total,
        "by_category": by_category,
        "by_status": by_status,
        "posture": "HYBRID | ADAPTIVE | trophallaxis_primed | v3.2.1+",
        "last_updated": "2026-07-01",
    }


# Convenience re-exports for HybridControlSwarmGraph integration
__all__ = [
    "SkillCategory",
    "SkillInfo",
    "SKILL_REGISTRY",
    "list_available_skills",
    "get_skill_info",
    "register_skill_extension",
    "get_skill_registry_summary",
]