"""
harness_adapter.py
Utilities for integrating HybridControlSwarmGraph with graph_swarm_harness/

This module provides adapters and helpers to make it easier to use the
production Graph Swarm Harness (from src/base_graph) inside the full
agent swarm orchestrator in graph_swarm_harness/.

Posture: HYBRID | ADAPTIVE | trophallaxis_primed | v3.2.1+
"""

from __future__ import annotations

from typing import Any, Dict

try:
    from .factory import HybridControlSwarmGraph
except ImportError:
    HybridControlSwarmGraph = None


def hybrid_control_to_harness_state(
    swarm: "HybridControlSwarmGraph"
) -> Dict[str, Any]:
    """
    Convert a HybridControlSwarmGraph into a dictionary format that can be
    more easily consumed by graph_swarm_harness/harness/dashboard.py
    or similar components.

    This is a starting point for integration between the library and
    the full application layer.
    """
    if HybridControlSwarmGraph is None:
        raise ImportError("HybridControlSwarmGraph not available")

    health = swarm.get_health()
    metrics = swarm.get_metrics()

    return {
        "swarm_name": swarm.name,
        "tick": None,
        "emergence_level": health["emergence_level"],
        "node_count": health["node_count"],
        "edge_count": health["edge_count"],
        "control_mode": health["control_mode"],
        "posture": health.get("posture", {}),
        "metrics": metrics.get("metrics", {}),
        "last_checkpoint": health.get("last_checkpoint"),
        "nodes": {
            nid: {
                "id": nid,
                "role": node.role,
                "health": node.health,
                "opinions": node.opinions,
            }
            for nid, node in swarm.nodes.items()
        },
        "edges": swarm.edges,
    }


def get_swarm_health_for_harness(swarm: "HybridControlSwarmGraph") -> Dict[str, Any]:
    """Return a compact health dict suitable for the harness dashboard."""
    return swarm.get_health()


if __name__ == "__main__":
    from .factory import create_recommended_swarm

    swarm = create_recommended_swarm(num_agents=24, name="adapter-test")
    for _ in range(2):
        swarm.hybrid_step()

    print("HybridControlSwarmGraph -> harness compatible state:")
    state = hybrid_control_to_harness_state(swarm)
    print(f"  Name: {state['swarm_name']}")
    print(f"  Emergence: {state['emergence_level']}")
    print(f"  Nodes: {state['node_count']}")
    print(f"  Sample node keys: {list(state['nodes'].keys())[:3]}")