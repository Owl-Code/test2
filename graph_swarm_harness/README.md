# Graph Swarm Harness (`graph_swarm_harness`)

This harness is a production-grade, local-LLM-powered orchestration environment for agent swarms. It integrates the `base_graph` primitives (EmergenceNode, AdaptiveEdge, Trophallaxis, and Provenance) with an execution loop powered by local Ollama inference (`qwen2.5:3b-instruct`).

## 1. System Architecture

The harness coordinates autonomous agents via a **hybrid control graph**:
- **Core Primitives**: Each agent is an `EmergenceNode` whose custom role, beliefs, and skills are stored dynamically inside its serialized state.
- **Sparse Activation**: To minimize token consumption and inference latency on local hardware, a custom expert router activates only 1–2 agents per tick (prioritizing the central coordinator and agents with pending inbox messages).
- **Trophallaxis & Metabolism**: Agents burn energy (2.5% per action, 0.5% when idle) and automatically share resources along `TrophallaxisEdges` when neighbors fall below safe homeostatic limits.
- **Stigmergic Pheromones**: Successful collaborations reinforce virtual pheromone levels on connecting edges, biasing future message routes.
- **Cryptographic Provenance**: Every state mutation is hashed (SHA-256) and chained, preventing tampering and enabling complete rollback.
- **Safety Gate**: Any command flagged with a `HIGH` risk level (such as `execute_python_snippet` or `write_file`) is halted until manually confirmed by the human operator via a CLI prompt.

## 2. Capabilities Registries

### Tools (Atomic Actions)
- `read_file`: Reads text contents of a file inside the workspace.
- `write_file`: Writes content to a file inside the workspace (requires operator approval).
- `list_dir`: Lists files in a directory.
- `execute_python_snippet`: Executes Python scripts in an isolated subprocess (requires operator approval).
- `update_swarm_node_state`: Modifies node variables.
- `query_swarm_emergence`: Computes cohesion levels.
- `create_handoff_edge`: Places a message in a peer's inbox.
- `diffuse_signal`: Spreads pheromones.

### Skills (Workflows)
- `code_execution`: Compiles and runs logic.
- `file_io`: Higher-order file management.
- `graph_query` / `graph_update`: Graph topology queries.
- `handoff_create`: Delegates task to a peer agent.
- `trophallaxis_exchange`: Swarms local energy.
- `self_reflect_and_emergence_update`: Evaluates node cohesion.
- `spawn_sub_agent`: Dynamically spawns a child specialist agent.
- `set_control_mode`: Modifies orchestration regimes.
- `skill_invoke`: Runs nested sub-skills.

## 3. Getting Started

### Run the Swarm Loop
Create and execute a script (e.g. `run_harness.py`) at the root:
```python
from graph_swarm_harness.harness.main_loop import SwarmHarnessOrchestrator

orchestrator = SwarmHarnessOrchestrator(config_path="graph_swarm_harness/config.yaml")
orchestrator.setup_swarm(resume=False)  # Bootstraps coordinator agent

# Runs 10 execution ticks with a 1-second delay
orchestrator.loop(ticks=10, delay=1.0)
```
To run it:
```bash
python run_harness.py
```
If a `HIGH` risk action is proposed, approval is requested:
```text
========== SAFETY GATE: HIGH-RISK ACTION ==========
Agent: agent_a8f3b2
Action: write_file
Arguments: {
  "path": "test.txt",
  "content": "Hello Swarm!"
}
Rationale: Writing test files for task verification.
===================================================
Approve execution? [y/N]: y
```
