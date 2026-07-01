"""
phase2_factory_demo.py
Demonstration of the Phase 2 Production Factory (create_recommended_swarm)

Shows the recommended bootstrap in action:
- Creating a swarm with create_recommended_swarm(num_agents=64)
- Running hybrid steps with expert routing and auto-checkpointing
- Inspecting posture, health, metrics, and the integrated textual dashboard

Run with:
    python examples/phase2_factory_demo.py

Part of the autonomous SOTA evolution on grok_branch (v3.2.1-dev)
"""

from __future__ import annotations

from base_graph import (
    create_recommended_swarm,
    HybridControlSwarmGraph,
    SwarmPosture,
)


def main():
    print("=" * 72)
    print("base_graph Phase 2 Factory Demo — create_recommended_swarm + Graph Swarm Harness")
    print("Posture: HYBRID | ADAPTIVE | trophallaxis_primed | v3.2.1-dev")
    print("=" * 72)

    # 1. Bootstrap a recommended swarm
    print("\n[1] Creating recommended swarm (target 64 agents)")
    swarm: HybridControlSwarmGraph = create_recommended_swarm(
        num_agents=64,
        name="phase2-demo-swarm",
        use_fs_graph=True,
        enable_expert_routing=True,
        enable_trophallaxis_handoff=True,
    )

    print(f"    Swarm name: {swarm.name}")
    print(f"    Target agents: {swarm.num_agents_target}")
    print(f"    Initial nodes created: {len(swarm.nodes)}")
    print(f"    Bootstrap checkpoint: {swarm._checkpoint_sha[:16]}...")
    print(f"    Initial emergence: {swarm.emergence_level:.3f}")

    # 2. Run several hybrid steps
    print("\n[2] Running hybrid steps (with auto expert routing + checkpointing)")
    for i in range(5):
        result = swarm.hybrid_step({"task_complexity": 0.85 + i * 0.02})
        print(f"    Step {i+1}: emergence={result['emergence']:.3f}, "
              f"experts={len(result['experts_activated'])}, "
              f"active_nodes={result['active_nodes']}")

    # 3. Observability
    print("\n[3] Observability (get_health + get_metrics)")
    health = swarm.get_health()
    print(f"    Emergence: {health['emergence_level']:.3f} | Nodes: {health['node_count']} | Mode: {health['control_mode']}")

    # 4. Integrated Graph Swarm Harness Dashboard (new render_dashboard method)
    print("\n[4] Integrated Graph Swarm Harness Dashboard")
    print(swarm.render_dashboard())

    # 5. Manual checkpoint
    print("\n[5] Manual checkpoint")
    manual_sha = swarm.checkpoint(name="phase2_demo_manual")
    print(f"    Manual checkpoint SHA: {manual_sha[:16]}...")

    print("\n" + "=" * 72)
    print("Phase 2 Factory Demo Complete — create_recommended_swarm + Graph Swarm Harness is fully operational.")
    print("The harness now includes nodes, expert routing, auto-checkpointing, health/metrics, and integrated textual dashboard.")
    print("=" * 72)


if __name__ == "__main__":
    main()