 """
phase1_showcase.py
Demonstration of Phase 1 SOTA Extensions for base_graph

Shows the new capabilities working together:
- Dynamic 56-skill registry
- SHA-256 fs-graph checkpointing
- Emergence-gated expert routing (MoE style)
- Trophallaxis-aware planning handoffs

Run with:
    python examples/phase1_showcase.py

Part of the autonomous SOTA evolution on grok_branch (v3.2.1-dev)
"""

from __future__ import annotations

from base_graph import (
    # Skill Registry
    list_available_skills,
    get_skill_registry_summary,
    SkillCategory,
    register_skill_extension,

    # FS Graph
    save_checkpoint,
    load_checkpoint,
    list_checkpoints,

    # Expert Routing
    create_emergence_gated_router,
    EmergenceGatedRouter,

    # Trophallaxis Handoff
    create_trophallaxis_handoff_hook,
    resource_aware_plan_handoff,
    HandoffContext,
)


def main():
    print("=" * 70)
    print("base_graph Phase 1 Showcase — Hybrid Control Swarm Harness v3.2.1-dev")
    print("Posture: HYBRID | ADAPTIVE | trophallaxis_primed")
    print("=" * 70)

    # 1. Skill Registry
    print("\n[1] Dynamic Skill Registry (56 skills)")
    summary = get_skill_registry_summary()
    print(f"    Total skills: {summary['total_skills']}")
    print(f"    By category count: {len(summary['by_category'])}")
    print(f"    Core skills: {summary['by_status'].get('core', 0)}")
    print(f"    Live skills: {summary['by_status'].get('live', 0)}")

    # Show a few advanced reasoning skills
    reasoning_skills = list_available_skills(category=SkillCategory.ADVANCED_REASONING)
    print(f"    Advanced Reasoning skills available: {len(reasoning_skills)}")
    for s in reasoning_skills[:3]:
        print(f"      - {s.name}: {s.description[:60]}...")

    # Register a custom extension (demonstrates extensibility)
    register_skill_extension(
        name="custom-emergence-analyzer",
        description="User-defined emergence metric analyzer for specific domains.",
        category=SkillCategory.ADVANCED_REASONING,
        tags=["custom", "emergence"],
    )
    print("    ✓ Registered custom extension 'custom-emergence-analyzer'")

    # 2. FS Graph Checkpointing
    print("\n[2] FS-Graph SHA-256 Checkpointing")
    state = {
        "control_mode": "HYBRID",
        "node_count": 48,
        "edge_count": 127,
        "emergence_level": 0.87,
        "last_handoff": "planner_alpha → cluster_beta",
    }
    sha, path = save_checkpoint(state, name="phase1_demo_checkpoint", swarm_name="showcase-swarm")
    print(f"    Saved checkpoint: {path.name}")
    print(f"    SHA256 (truncated): {sha[:16]}...")

    loaded = load_checkpoint(sha[:12])  # load by prefix
    print(f"    Loaded successfully. Emergence in checkpoint: {loaded['state']['emergence_level']}")

    checkpoints = list_checkpoints()
    print(f"    Total checkpoints on disk: {len(checkpoints)}")

    # 3. Emergence-Gated Expert Routing
    print("\n[3] Emergence-Gated MoE Expert Routing")
    router = create_emergence_gated_router(k=3, emergence_target=0.92)
    context = {
        "emergence_level": 0.89,
        "task_complexity": 0.95,
    }
    decision = router.route(
        ["base-graph", "diffusion-graph", "meta-skill-evolver",
         "planner-graph", "philosophy", "trophallaxis-graph-skill"],
        context=context,
    )
    print(f"    Selected top-{decision.k} experts: {decision.selected_experts}")
    print(f"    Rationale: {decision.rationale}")

    # 4. Trophallaxis-Aware Planning Handoff
    print("\n[4] TrophallaxisPlannerHandoffHook (resource-aware)")
    hook = create_trophallaxis_handoff_hook(efficiency_base=0.87)
    ctx = HandoffContext(
        source_planner="planner_alpha",
        target_cluster="cluster_beta",
        task_tokens_deficit=0.42,
        evidence_confidence_deficit=0.28,
        current_emergence=0.89,
        priority=1.2,
    )
    transfers = hook.perform_handoff(
        ctx,
        source_resources={"task_tokens": 1.0},
        target_resources={"evidence_confidence": 0.92},
    )
    print(f"    Transfers executed: {len(transfers)}")
    for t in transfers:
        print(f"      {t.resource_type}: {t.amount:.3f} from {t.from_node} → {t.to_node} "
              f"(eff={t.efficiency:.2f})")

    summary = hook.get_transfer_summary()
    print(f"    Handoff summary: {summary['total_transfers']} transfers, "
          f"task_tokens={summary.get('total_task_tokens_transferred', 0):.3f}")

    # 5. Integrated resource_aware_plan_handoff stub
    print("\n[5] High-level resource_aware_plan_handoff integration stub")
    transfers2 = resource_aware_plan_handoff(
        source_planner={"id": "planner_main"},
        target_cluster={"id": "execution_cluster"},
        context={"task_deficit": 0.35, "evidence_deficit": 0.22, "emergence": 0.91},
    )
    print(f"    Stub executed {len(transfers2)} transfers (demonstration)")

    print("\n" + "=" * 70)
    print("Phase 1 Showcase Complete — All new modules working together successfully.")
    print("Posture maintained: HYBRID | ADAPTIVE | trophallaxis_primed | v3.2.1-dev")
    print("=" * 70)


if __name__ == "__main__":
    main()