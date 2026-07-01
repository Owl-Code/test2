"""
textual_dashboard.py
Minimal Textual Dashboard for HybridControlSwarmGraph and compatible systems (Phase 3 starter)

Provides simple, human-readable health and metrics rendering.
Designed to work with both:
- HybridControlSwarmGraph instances (from src/base_graph)
- Plain dictionaries (e.g. from to_observability_dict() or graph_swarm_harness/)

This makes it easier to integrate with external systems like graph_swarm_harness/harness/dashboard.py.

Posture: HYBRID | ADAPTIVE | trophallaxis_primed | v3.2.1+
"""

from __future__ import annotations

from typing import Any, Dict, Union

def _extract_data(source: Any) -> Dict[str, Any]:
    """Normalize input to a standard dict."""
    if isinstance(source, dict):
        return source
    if hasattr(source, "to_observability_dict"):
        return source.to_observability_dict()
    raise TypeError("Input must be a dict or have a to_observability_dict method")


def render_textual_dashboard(
    source: Union[Dict[str, Any], "HybridControlSwarmGraph"],
    width: int = 72
) -> str:
    """
    Render a clean textual dashboard.

    Accepts either:
    - A HybridControlSwarmGraph instance
    - A dictionary (e.g. from to_observability_dict() or external systems)
    """
    data = _extract_data(source)

    lines = []
    lines.append("=" * width)
    lines.append(f"  {data.get('swarm_name', data.get('name', 'Swarm'))}  |  Textual Dashboard")
    lines.append("=" * width)

    # Core status
    emergence = data.get("emergence_level", data.get("emergence", 0.0))
    nodes = data.get("node_count", 0)
    edges = data.get("edge_count", 0)
    mode = data.get("control_mode", "HYBRID")

    lines.append(f"Mode: {mode:12}   Emergence: {emergence:.3f}")
    lines.append(f"Nodes: {nodes:5}        Edges: {edges:5}")

    last_cp = data.get("last_checkpoint")
    if last_cp:
        lines.append(f"Last Checkpoint: {last_cp}")

    # Posture
    posture = data.get("posture", {})
    if posture:
        lines.append("-" * width)
        lines.append("Posture:")
        for k, v in posture.items():
            lines.append(f"  {k:22}: {v}")

    # Metrics
    metrics = data.get("metrics", {})
    if metrics:
        lines.append("-" * width)
        lines.append("Metrics:")
        for k, v in metrics.items():
            lines.append(f"  {k:22}: {v}")

    # Sample nodes (if available)
    sample = data.get("active_nodes_sample", [])
    if sample:
        lines.append("-" * width)
        lines.append("Sample Nodes:")
        for node in sample[:3]:
            lines.append(f"  {node.get('id', '?'):12} | {node.get('role', 'generalist'):10} | health={node.get('health', 0):.2f}")

    lines.append("=" * width)
    lines.append("  HYBRID | ADAPTIVE | trophallaxis_primed | Graph Swarm Harness")
    lines.append("=" * width)

    return "\n".join(lines)


def print_dashboard(source: Union[Dict[str, Any], "HybridControlSwarmGraph"]) -> None:
    """Print dashboard directly."""
    print(render_textual_dashboard(source))


if __name__ == "__main__":
    from .factory import create_recommended_swarm

    swarm = create_recommended_swarm(num_agents=32, name="integration-test")
    for _ in range(3):
        swarm.hybrid_step()

    print("Using HybridControlSwarmGraph instance:")
    print_dashboard(swarm)

    print("\nUsing to_observability_dict():")
    print_dashboard(swarm.to_observability_dict())