# Base Graph Swarm Harness (`base_graph`)

> "This library exists to help humanity understand and build systems where intelligence emerges from local interactions, where swarms become antifragile through stigmergy and trophallaxis, where every decision carries provenance, and where hybrid control gives humans both powerful leverage and absolute override authority. We favor emergence and positive-sum dynamics over brittle central control."

**SOTA Evolution Active on `grok_branch`**  
See the live **[SOTA Development Plan](SOTA_DEVELOPMENT_PLAN.md)** for the complete phased roadmap to evolve this into the canonical production-grade **Hybrid Control Swarm Harness v3.2.1+**.

**Current Posture**: `HYBRID | ADAPTIVE | trophallaxis_primed | fs-graph active | full_skill_exposure targeted | human_override=absolute`

`base_graph` is the foundational layer for the **Graph Swarm Harness** — a production-grade, local-first Python package for emergent, provenance-rich, hybrid-controlled swarm systems.

---

## Graph Swarm Harness Quickstart (Recommended)

```python
from base_graph import create_recommended_swarm, render_textual_dashboard

# Create a fully wired production swarm (Phase 2 factory)
swarm = create_recommended_swarm(
    num_agents=128,
    name="my-graph-swarm",
    use_fs_graph=True,
    enable_expert_routing=True,
)

# Run hybrid steps (includes expert routing + auto-checkpointing)
for _ in range(5):
    swarm.hybrid_step({"task_complexity": 0.9})

# View integrated textual dashboard (Phase 3)
print(swarm.render_dashboard())
# or: print(render_textual_dashboard(swarm))

# Inspect health & metrics
print(swarm.get_health())
```

See `examples/phase2_factory_demo.py` for a complete runnable example.

---

## Installation

```bash
git clone -b grok_branch https://github.com/owl-code/test2.git
cd test2
python -m venv .venv && source .venv/bin/activate
pip install -e .[dev]
```

---

## Core Principles

1. **Local-First & Lightweight**
2. **Cryptographic Provenance** (SHA-256)
3. **Trophallaxis** (resource homeostasis)
4. **Stigmergic Adaptation**
5. **Absolute Human Override**

---

## Development Status (v3.2.1-dev)

**Phase 1 (Complete)**: 56-skill registry, fs-graph checkpointing, EmergenceGatedRouter, TrophallaxisPlannerHandoffHook.

**Phase 2 (Complete)**: `create_recommended_swarm()` factory, enhanced `HybridControlSwarmGraph` with nodes/edges/health/metrics + `render_dashboard()`.

**Phase 3 (Started)**: Minimal textual dashboard rendering.

See the full [SOTA Development Plan](SOTA_DEVELOPMENT_PLAN.md) for the roadmap.

---

## License

MIT