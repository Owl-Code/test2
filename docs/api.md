# Base Graph API Reference

This document describes the primary classes and interfaces exposed by the `base_graph` library.

---

## 1. Types & Enums (`base_graph.types`)

### `ControlMode`
An enumeration representing how nodes or subgraphs make decisions and route control.
- `HIERARCHICAL`: Directed command propagation from parent/leader nodes to children.
- `DECENTRALIZED`: Local opinion dynamics, diffusion, and consensus.
- `STIGMERGIC`: Environment-mediated communication (pheromones, weight modifications).
- `EMERGENCE`: Pure local interactions with no predefined global coordinator.

### `EdgeType`
Supported interaction profiles for edges:
- `COMMUNICATION`
- `COMMAND`
- `RESOURCE`
- `INFLUENCE`
- `STIGMERGY`
- `TROPHALLAXIS`

---

## 2. Primitives

### `EmergenceNode` (`base_graph.primitives.node`)
Inherits from `BaseNode`. Represents an active agent inside the swarm.
- **Attributes**:
  - `id`: Unique identifier (string or UUID)
  - `state`: Local state dictionary
  - `resources`: Dictionary mapping resource names (e.g., `"energy"`) to float values
  - `opinions`: Dictionary mapping topics to float values in `[-1.0, 1.0]`
  - `goals`: List of active goals/targets
  - `control_mode`: The active `ControlMode`
- **Methods**:
  - `local_step(context)`: Executed on every step. Evaluates local conditions and acts.
  - `receive_trophallaxis(resource_type, amount, from_node)`: Safe entry for resource additions.
  - `deposit_stigmergy(signal, intensity, edge_id)`: Deposits signals onto an edge.
  - `compute_local_contribution_to_emergence()`: Computes how aligned the node's actions are with neighbors.

### `AdaptiveEdge` / `TrophallaxisEdge` (`base_graph.primitives.edge`)
- **Attributes**:
  - `source_id`, `target_id`: Node IDs
  - `weight`: Edge weight
  - `edge_type`: `EdgeType`
  - `strength`: Antifragility coefficient (strengthens with positive usage)
- **Methods**:
  - `update_weight(delta, reason, provenance)`: Adjusts weight and log.
  - `propagate(value, decay)`: Propagates signals down the edge.
  - `transfer(from_node, to_node, resource, amount)`: Safely transfers resources.

### `BaseGraph` (`base_graph.primitives.graph`)
The core structural container.
- **Methods**:
  - `add_node(node)`, `remove_node(node_id)`
  - `add_edge(edge)`, `remove_edge(edge_id)`, `rewire(edge_id, new_target_id)`
  - `get_neighbors(node_id, edge_type_filter)`
  - `to_adjacency_matrix(sparse)`: Returns representation.
  - `laplacian_matrix(normalized)`: Computes normalized Laplacian.
  - `subgraph(node_ids)`: Creates sub-graph views.

---

## 3. Swarm Core

### `HybridControlSwarmGraph` (`base_graph.core.hybrid_swarm`)
The main coordinator of the swarm.
- **Methods**:
  - `hybrid_step(global_context)`: Steps every node, updates edges, logs provenance, and updates metrics.
  - `set_control_mode(mode)`: Updates the control modes globally or selectively.
  - `compute_swarm_health()`: Computes entropy, spectral gap, and composite emergence level.
  - `checkpoint()`: Creates an audited state snapshot.
  - `restore(checkpoint)`: Rolls back/forward to a previous checkpoint.
  - `register_skill_extension(name, extension)`: Registers custom routines.
