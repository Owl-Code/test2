# Base Graph Swarm Harness (`base_graph`)

> "This library exists to help humanity understand and build systems where intelligence emerges from local interactions, where swarms become antifragile through stigmergy and trophallaxis, where every decision carries provenance, and where hybrid control gives humans both powerful leverage and absolute override authority. We favor emergence and positive-sum dynamics over brittle central control."

**SOTA Evolution Active on `grok_branch`**  
See the live **[SOTA Development Plan](SOTA_DEVELOPMENT_PLAN.md)** for the complete phased roadmap to evolve this into the canonical production-grade **Hybrid Control Swarm Harness v3.2.1+** (full 56-skill dynamic exposure, 512-agent factory, live fs-graph SHA256 checkpoints, meta-skill-evolver, dashboard-graph, simulation-harness, constitutional alignment, and automated reporting).  

**Current Posture**: `HYBRID | ADAPTIVE | trophallaxis_primed | fs-graph active | full_skill_exposure targeted | human_override=absolute`  
**Pushing Protocol**: Every update is pushed immediately via connected GitHub tooling with full provenance in commit messages.

`base_graph` is a production-grade, local-first Python package that realizes the foundational primitives for **Dynamic Graph Swarm Harnesses**. It provides the core structures for nodes, adaptive edges, local-decision routing, and information diffusion models.

---

## 1. Core Principles

1. **Local-First & Lightweight**: Zero external network calls. Built using Python 3.11+, Pydantic v2, and standard numerical stacks (`numpy` / `scipy` with pure-Python fallbacks).
2. **Cryptographic Provenance**: Every state mutation (add, delete, rewire, resource transfer, mode update) generates an audited State Delta appended to a hash-linked cryptographic chain (SHA-256).
3. **Homeostatic Homeostasis (Trophallaxis)**: Local sharing protocols model energy/resource distribution to maintain global swarm equilibrium under metabolic stress.
4. **Stigmergic Adaptation**: Edges act as virtual pheromone channels, reinforcing path weights dynamically to form global structure from local actions (antifragile adaptation).
5. **Absolute Human Override**: Complete escape hatches are provided to allow external operators to inject command decisions that override agent heuristics immediately.

---

## 2. Architecture

```mermaid
graph TD
    subgraph Swarm Environment
        N1[EmergenceNode 1] <-->|Trophallaxis Edge| N2[EmergenceNode 2]
        N1 -->|Stigmergic Pheromone Deposit| E1[AdaptiveEdge]
        N2 -->|Stigmergic Pheromone Deposit| E1
        E1 -->|Feedback Loop| N1
        E1 -->|Feedback Loop| N2
    end

    subgraph Hybrid Control Orchestrator
        HC[HybridControlSwarmGraph] -->|Read State| M[Metrics: Spectral Gap / Entropy]
        HC -->|Step / Control Mode| N1
        HC -->|Step / Control Mode| N2
        HC -->|Commit State Change| P[Provenance Chain]
    end

    Human[Human Operator] -.->|Override / Control Switching| HC
```

---

## 3. Requirements Satisfaction Matrix

| Directive | Description | Implementation Details |
|---|---|---|
| **1. Truth & Mathematical Rigor** | Spectral methods, Normalized Laplacian, Algebraic connectivity | Implemented in `core/metrics.py` (spectral gap, Shannon entropy) using NumPy and pure-Python fallbacks. Formula definitions in `docs/math.md`. |
| **2. Emergence over Central Control** | Decoupled local rules, opinion dynamics, stubs | Nodes route actions locally using `node.decide()`. Stigmergy & Trophallaxis manage resource flows without global scheduling. |
| **3. Stigmergy + Trophallaxis** | Local resource sharing, pheromone reinforcement | `primitives/edge.py` implements `TrophallaxisEdge` and `EmergenceEdge` with decay and usage strength updates. |
| **4. Provenance & Verifiability** | Cryptographic hash chaining, auditing, restore checkpoints | `core/provenance.py` implements append-only `ProvenanceChain` (SHA-256) and `Checkpoint` hashing to enable rollback (`restore`). |
| **5. Hybrid Control Primitives** | Switchable control regimes (Hierarchical, Decentralized, etc.) | `core/hybrid_swarm.py` implements `set_control_mode` and routes steps based on `ControlMode` enum. |
| **6. Human Override Absolute** | Immediate command execution and priority override | Heuristics inside `EmergenceNode.decide` check for human override signals in the incoming step context to skip agent rules. |
| **7. Extensibility Hooks** | Clean entry points for downstream MCP / swarm skills | Custom strategies can be registered via `HybridControlSwarmGraph.register_skill_extension()` and overriding `node.policy`. |
| **8. Antifragility & Eudaimonia** | System grows stronger under beneficial usage/stress | `AdaptiveEdge.strength` accumulates on usage, buffering signal decay. Documented human-centered philosophy in README. |
| **9. Robustness & Production Quality** | Pydantic v2 validation, type hints, complete test coverage | Strict typing, Pydantic configuration models, and unit tests with >80% coverage. |

---

## 4. Installation & Quickstart

### Prerequisites
- Python 3.11+
- Virtual environment (recommended)

### Local Development Setup
Clone and install the package locally in editable mode:

```bash
# Clone the repository (or your fork)
git clone -b grok_branch https://github.com/owl-code/test2.git
cd test2

# Setup virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install package with development dependencies
pip install -e .[dev]
```

### Quickstart Example (Phase 1)
Create a simple swarm and run opinion consensus:

```python
from base_graph import HybridControlSwarmGraph, EmergenceNode, ControlMode
from base_graph import list_available_skills, create_emergence_gated_router

# List available skills (Phase 1+)
skills = list_available_skills()
print(f"Available skills: {len(skills)}")

# Create router
router = create_emergence_gated_router(k=3)
```

### Phase 2 — Recommended Production Bootstrap (New in v3.2.1+)

The canonical way to create a production-grade swarm:

```python
from base_graph import create_recommended_swarm, HybridControlSwarmGraph

# Create a fully wired recommended swarm (Phase 2 factory)
swarm: HybridControlSwarmGraph = create_recommended_swarm(
    num_agents=128,
    name="my-production-swarm",
    use_fs_graph=True,
    enable_expert_routing=True,
    enable_trophallaxis_handoff=True,
)

print(f"Created: {swarm.name}")
print(f"Initial nodes: {len(swarm.nodes)}")
print(f"Posture: {swarm.get_posture().__dict__}")

# Run hybrid steps (includes expert routing + auto-checkpointing)
for _ in range(5):
    result = swarm.hybrid_step({"task_complexity": 0.9})
    print(f"Emergence: {result['emergence']:.3f} | Experts: {result['experts_activated']}")

# Manual checkpoint
sha = swarm.checkpoint("my_checkpoint")
print(f"Checkpoint: {sha[:16]}...")
```

See `examples/phase2_factory_demo.py` for a complete runnable example.

---

## 5. Verification Validation

To run all mathematical tests and execute the 5 core demo scripts:

```bash
python scripts/validate_install.py
```

This script will execute:
1. `pytest` unit test runs.
2. `01_simple_emergence.py` - Emergence level growth.
3. `02_diffusion_opinion_dynamics.py` - Polarization vs consensus.
4. `03_stigmergy_foraging.py` - Pheromone path optimization.
5. `04_hybrid_mode_switching.py` - Control mode handoffs.
6. `05_trophallaxis_homeostasis.py` - Metabolic resource distributions.

---

## 6. Development Status & SOTA Roadmap (v3.2.1+)

This repository is under active **SOTA evolution** on the `grok_branch`. The [SOTA Development Plan](SOTA_DEVELOPMENT_PLAN.md) defines a 6-phase roadmap with a strict **push-every-update** protocol:

**Phase 1 (Complete)**: Dynamic 56-skill registry, SHA-256 fs-graph checkpointing, EmergenceGatedRouter (MoE), TrophallaxisPlannerHandoffHook, clean package exposure, and runnable showcase.

**Phase 2 (In Progress)**: Production `create_recommended_swarm(num_agents=512)` factory with wired Phase 1 capabilities, improved `HybridControlSwarmGraph` skeleton (nodes, edges, `hybrid_step`, posture), and runnable demo.

**Phase 3+ (Planned)**: Live `dashboard_graph` + long-horizon metrics, `meta_skill_evolver`, `simulation_harness_graph`, multi-scale planning (`planner_graph` + `mcp_graph`), constitutional alignment, and automated reporting.

**All changes are pushed immediately** with conventional commits containing posture, provenance SHA256, and skill alignment notes. High-stakes changes require explicit human confirmation.

**Current version target**: 3.2.1-dev (see `pyproject.toml`).

---

## License

MIT — see LICENSE file.