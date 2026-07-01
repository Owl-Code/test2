 """
textual_dashboard.py
Minimal Textual Dashboard for HybridControlSwarmGraph (Phase 3 starter)

Provides simple, human-readable health and metrics rendering.
Designed to be lightweight and usable immediately while the full
dashboard_graph (matplotlib + rich visuals) is developed in Phase 3.

Usage:
    from base_graph import create_recommended_swarm
    from base_graph.textual_dashboard import render_textual_dashboard

    swarm = create_recommended_swarm(num_agents=64)
    for _ in range(3):
        swarm.hybrid_step()
    print(render_textual_dashboard(swarm))

Posture: HYBRID | ADAPTIVE | trophallaxis_primed | v3.2.1+
"""

from __future__ import annotations

from typing import Any, Dict


from .factory import HybridControlSwarmGraph


def render_textual_dashboard(swarm: HybridControlSwarmGraph, width: int = 72) -> str:
    """
    Render a clean textual dashboard for a HybridControlSwarmGraph.
    """
    health = swarm.get_health()
    metrics = swarm.get_metrics()

    lines = []
    lines.append("=" * width)
    lines.append(f"  {swarm.name}  |  Textual Dashboard (v3.2.1-dev)")
    lines.append("=" * width)

    # Core status
    lines.append(f"Mode: {health['control_mode']:12}   Emergence: {health['emergence_level']:.3f}")
    lines.append(f"Nodes: {health['node_count']:5}        Edges: {health['edge_count']:5}")
    lines.append(f"Skills: {health['skill_count']:4}        Last Checkpoint: {health.get('last_checkpoint', 'N/A')}")

    # Posture block
    posture = health.get("posture", {})
    lines.append("-" * width)
    lines.append("Posture:")
    for k, v in posture.items():
        lines.append(f"  {k:22}: {v}")

    # Metrics / trends
    m = metrics.get("metrics", {})
    if m:
        lines.append("-" * width)
        lines.append("Metrics:")
        for k, v in m.items():
            lines.append(f"  {k:22}: {v}")

    lines.append("=" * width)
    lines.append("  HYBRID | ADAPTIVE | trophallaxis_primed | fs-graph + expert routing active")
    lines.append("=" * width)

    return "\n".join(lines)


def print_dashboard(swarm: HybridControlSwarmGraph) -> None:
    """Convenience wrapper that prints the dashboard directly."""
    print(render_textual_dashboard(swarm))


if __name__ == "__main__":
    from .factory import create_recommended_swarm

    swarm = create_recommended_swarm(num_agents=48, name="dashboard-test-swarm")
    for _ in range(4):
        swarm.hybrid_step({"task_complexity": 0.8})

    print_dashboard(swarm)