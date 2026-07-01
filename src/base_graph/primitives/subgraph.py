import math
from typing import Dict, List, Set, Tuple, Union, Any, Optional
from dataclasses import dataclass, field
from base_graph.primitives.graph import BaseGraph
from base_graph.primitives.node import EmergenceNode

try:
    import numpy as np
except ImportError:
    np = None  # type: ignore

@dataclass
class DiffusionTrajectory:
    model: str
    steps_run: int
    history: List[Dict[str, Dict[str, float]]] = field(default_factory=list)
    entropy_curve: List[float] = field(default_factory=list)
    consensus_time: Optional[int] = None
    final_state: Dict[str, Dict[str, float]] = field(default_factory=dict)

class DiffusionSubgraph(BaseGraph):
    def __init__(self, parent_graph: Optional[BaseGraph] = None) -> None:
        super().__init__()
        if parent_graph:
            # Shallow copy references to nodes and edges
            self.nodes = parent_graph.nodes
            self.edges = parent_graph.edges
            self._adjacency_list = parent_graph._adjacency_list
            self._reverse_adjacency_list = parent_graph._reverse_adjacency_list

    def run_diffusion(self, model: str = "opinion", steps: int = 50, params: Optional[Dict[str, Any]] = None) -> DiffusionTrajectory:
        """Runs a diffusion model across the node states.
        
        Supported models:
          - "opinion": Bounded confidence DeGroot/HK opinion convergence.
          - "heat": Heat equation discrete steps.
          - "sir": Epidemiological compartment propagation.
        """
        if params is None:
            params = {}

        if model == "opinion":
            return self._run_opinion_diffusion(steps, params)
        elif model == "heat":
            return self._run_heat_diffusion(steps, params)
        elif model == "sir":
            return self._run_sir_diffusion(steps, params)
        else:
            raise ValueError(f"Unknown diffusion model: {model}")

    def _run_opinion_diffusion(self, steps: int, params: Dict[str, Any]) -> DiffusionTrajectory:
        epsilon = params.get("epsilon", 0.5)
        topic = params.get("topic", "main")
        
        trajectory = DiffusionTrajectory(model="opinion", steps_run=0)
        
        # Initial opinions
        current_opinions = {}
        for nid, node in self.nodes.items():
            if isinstance(node, EmergenceNode):
                current_opinions[nid] = node.opinions.get(topic, 0.0)
            else:
                current_opinions[nid] = node.state.setdefault("opinion", 0.0)
                
        # Record t=0
        trajectory.history.append({nid: {topic: val} for nid, val in current_opinions.items()})
        trajectory.entropy_curve.append(self._compute_opinion_entropy(current_opinions))
        
        consensus_step = None
        
        for step in range(1, steps + 1):
            next_opinions = {}
            for nid in self.nodes.keys():
                # Hegselmann-Krause opinion dynamic: average opinions of neighbors within epsilon
                neighbors = self.get_neighbors(nid)
                aligned_opinions = [current_opinions[nid]]
                
                for neigh in neighbors:
                    neigh_id = str(neigh.id)
                    neigh_op = current_opinions[neigh_id]
                    if abs(current_opinions[nid] - neigh_op) <= epsilon:
                        aligned_opinions.append(neigh_op)
                
                next_opinions[nid] = sum(aligned_opinions) / len(aligned_opinions)
            
            # Check for consensus (opinions are close)
            op_values = list(next_opinions.values())
            if op_values and max(op_values) - min(op_values) < 0.01 and consensus_step is None:
                consensus_step = step
                
            current_opinions = next_opinions
            trajectory.history.append({nid: {topic: val} for nid, val in current_opinions.items()})
            trajectory.entropy_curve.append(self._compute_opinion_entropy(current_opinions))
            
            if consensus_step is not None and params.get("stop_on_consensus", False):
                break

        trajectory.steps_run = len(trajectory.history) - 1
        trajectory.consensus_time = consensus_step
        trajectory.final_state = trajectory.history[-1]
        
        # Apply final opinion state back to nodes
        for nid, op_dict in trajectory.final_state.items():
            node = self.nodes[nid]
            if isinstance(node, EmergenceNode):
                node.opinions[topic] = op_dict[topic]
            else:
                node.state["opinion"] = op_dict[topic]
                
        return trajectory

    def _run_heat_diffusion(self, steps: int, params: Dict[str, Any]) -> DiffusionTrajectory:
        alpha = params.get("alpha", 0.1)  # Thermal conductivity/step size
        resource = params.get("resource", "energy")
        
        trajectory = DiffusionTrajectory(model="heat", steps_run=steps)
        
        # Get node identifiers order
        node_ids = sorted(list(self.nodes.keys()))
        n = len(node_ids)
        if n == 0:
            return trajectory
            
        id_map = {nid: idx for idx, nid in enumerate(node_ids)}
        
        # Initial values
        x = np.zeros(n) if np is not None else [0.0] * n
        for nid, node in self.nodes.items():
            val = 0.0
            if isinstance(node, EmergenceNode):
                val = node.resources.get(resource, 0.0)
            else:
                val = node.state.get(resource, 0.0)
            if np is not None:
                x[id_map[nid]] = val
            else:
                x[id_map[nid]] = val # type: ignore
                
        L = self.laplacian_matrix(normalized=True)
        
        # Record t=0
        history_step = {node_ids[i]: {resource: float(x[i])} for i in range(n)}
        trajectory.history.append(history_step)
        trajectory.entropy_curve.append(self._compute_heat_entropy(list(history_step.values()), resource))

        for step in range(1, steps + 1):
            if np is not None and isinstance(L, np.ndarray):
                # x_new = x - alpha * L * x
                x = x - alpha * (L @ x)
            else:
                # Pure Python Laplacian step: x_new_i = x_i - alpha * sum(L_ij * x_j)
                x_next = [0.0] * n
                for i in range(n):
                    lap_sum = sum(L[i][j] * x[j] for j in range(n)) # type: ignore
                    x_next[i] = x[i] - alpha * lap_sum # type: ignore
                x = x_next # type: ignore

            history_step = {node_ids[i]: {resource: float(x[i])} for i in range(n)}
            trajectory.history.append(history_step)
            trajectory.entropy_curve.append(self._compute_heat_entropy(list(history_step.values()), resource))

        trajectory.final_state = trajectory.history[-1]
        
        # Write back resources to nodes
        for nid, val_dict in trajectory.final_state.items():
            node = self.nodes[nid]
            if isinstance(node, EmergenceNode):
                node.resources[resource] = val_dict[resource]
            else:
                node.state[resource] = val_dict[resource]
                
        return trajectory

    def _run_sir_diffusion(self, steps: int, params: Dict[str, Any]) -> DiffusionTrajectory:
        beta = params.get("beta", 0.3)   # Infection probability
        gamma = params.get("gamma", 0.1) # Recovery probability
        
        trajectory = DiffusionTrajectory(model="sir", steps_run=steps)
        
        # SIR State represented as: S=0.0, I=1.0, R=2.0
        current_sir = {}
        for nid, node in self.nodes.items():
            # Standard initialization: Susceptible
            current_sir[nid] = node.state.setdefault("sir_status", 0.0)
            
        # If no infected is present, infect the first node
        if 1.0 not in current_sir.values():
            first_node = sorted(list(self.nodes.keys()))[0]
            current_sir[first_node] = 1.0
            self.nodes[first_node].state["sir_status"] = 1.0
            
        trajectory.history.append({nid: {"sir": val} for nid, val in current_sir.items()})
        trajectory.entropy_curve.append(self._compute_sir_entropy(current_sir))
        
        # Simple pseudorandom seed alignment
        import random
        rng = random.Random(params.get("seed", 42))

        for step in range(1, steps + 1):
            next_sir = current_sir.copy()
            for nid, status in current_sir.items():
                if status == 1.0:  # Infected
                    # Infect susceptible neighbors
                    neighbors = self.get_neighbors(nid)
                    for neigh in neighbors:
                        neigh_id = str(neigh.id)
                        if current_sir[neigh_id] == 0.0:
                            if rng.random() < beta:
                                next_sir[neigh_id] = 1.0
                    # Recover
                    if rng.random() < gamma:
                        next_sir[nid] = 2.0
                        
            current_sir = next_sir
            trajectory.history.append({nid: {"sir": val} for nid, val in current_sir.items()})
            trajectory.entropy_curve.append(self._compute_sir_entropy(current_sir))

        trajectory.final_state = trajectory.history[-1]
        
        # Update node state
        for nid, val_dict in trajectory.final_state.items():
            self.nodes[nid].state["sir_status"] = val_dict["sir"]
            
        return trajectory

    def _compute_opinion_entropy(self, opinions: Dict[str, float]) -> float:
        # Scale opinions from [-1.0, 1.0] to probabilities or count bins
        n = len(opinions)
        if n <= 1:
            return 0.0
        # Categorize into 5 bins
        bins = [0] * 5
        for op in opinions.values():
            # Map [-1.0, 1.0] to [0, 4]
            bin_idx = min(4, max(0, int((op + 1.0) * 2.5)))
            bins[bin_idx] += 1
            
        entropy = 0.0
        for count in bins:
            if count > 0:
                p = count / n
                entropy -= p * math.log2(p)
        return entropy / math.log2(5)

    def _compute_heat_entropy(self, heat_states: List[Dict[str, float]], resource: str) -> float:
        n = len(heat_states)
        if n <= 1:
            return 0.0
        values = [max(0.0, s[resource]) for s in heat_states]
        total = sum(values)
        if total == 0:
            return 1.0
            
        entropy = 0.0
        for val in values:
            p = val / total
            if p > 0:
                entropy -= p * math.log2(p)
        return entropy / math.log2(n)

    def _compute_sir_entropy(self, sir_states: Dict[str, float]) -> float:
        n = len(sir_states)
        if n <= 1:
            return 0.0
        counts = {0.0: 0, 1.0: 0, 2.0: 0}
        for status in sir_states.values():
            counts[status] = counts.get(status, 0) + 1
            
        entropy = 0.0
        for count in counts.values():
            if count > 0:
                p = count / n
                entropy -= p * math.log2(p)
        return entropy / math.log2(3)


class FractalSubgraph(BaseGraph):
    def __init__(self, parent_graph: Optional[BaseGraph] = None) -> None:
        super().__init__()
        if parent_graph:
            self.nodes = parent_graph.nodes
            self.edges = parent_graph.edges
            self._adjacency_list = parent_graph._adjacency_list
            self._reverse_adjacency_list = parent_graph._reverse_adjacency_list

    def detect_self_similar_clusters(self, threshold: float = 0.5) -> List[Set[str]]:
        """Identifies highly cohesive structural communities in the graph."""
        # Simple community detection based on edge weight thresholds
        visited = set()
        clusters = []
        
        for node_id in self.nodes.keys():
            if node_id not in visited:
                cluster = set()
                queue = [node_id]
                while queue:
                    curr = queue.pop(0)
                    if curr not in visited:
                        visited.add(curr)
                        cluster.add(curr)
                        
                        # Add outgoing and incoming neighbors where weights are strong
                        for edge_id, edge in self.edges.items():
                            if edge.weight >= threshold:
                                if edge.source_id == curr and edge.target_id not in visited:
                                    queue.append(edge.target_id)
                                elif edge.target_id == curr and edge.source_id not in visited:
                                    queue.append(edge.source_id)
                clusters.append(cluster)
        return clusters

    def multi_scale_view(self, levels: int = 2) -> Dict[str, Any]:
        """Generates nested subgraphs representing multi-scale aggregated resolutions."""
        view: Dict[str, Any] = {"level": 0, "nodes": list(self.nodes.keys()), "edges": list(self.edges.keys())}
        current_graph = self
        
        # Build nested resolutions
        for lvl in range(1, levels + 1):
            clusters = current_graph.detect_self_similar_clusters(threshold=0.5 + 0.1 * lvl)
            super_nodes = {}
            for idx, cluster in enumerate(clusters):
                super_nodes[f"SuperNode_{lvl}_{idx}"] = list(cluster)
                
            view[f"level_{lvl}"] = super_nodes
            
        return view

    def estimate_fractal_dimension(self) -> float:
        """Estimates the fractal dimension $d_B$ of the network topology.
        
        Uses box-counting mapping shortest path steps $l$ to box counts $N(l)$.
        """
        # Node diameter/distance calculation using BFS
        all_nodes = list(self.nodes.keys())
        n = len(all_nodes)
        if n <= 2:
            return 1.0
            
        # Compute shortest path distances (unweighted hop distances)
        dist = {}
        for src in all_nodes:
            dist[src] = {src: 0}
            queue = [src]
            visited = {src}
            while queue:
                curr = queue.pop(0)
                d = dist[src][curr]
                for neigh in self.get_neighbors(curr):
                    neigh_id = str(neigh.id)
                    if neigh_id not in visited:
                        visited.add(neigh_id)
                        dist[src][neigh_id] = d + 1
                        queue.append(neigh_id)
                        
        # Box size sizes
        box_sizes = [1, 2, 3, 4]
        box_counts = []
        
        for lb in box_sizes:
            # Estimate minimum boxes needed to cover graph such that no two nodes in a box are distance >= lb
            covered = set()
            boxes_count = 0
            for u in all_nodes:
                if u not in covered:
                    boxes_count += 1
                    # Put node and neighbors within distance lb - 1 in the box
                    in_box = {u}
                    for v in all_nodes:
                        if v in dist[u] and dist[u][v] < lb:
                            in_box.add(v)
                    covered.update(in_box)
            box_counts.append(boxes_count)
            
        # Log-log regression estimate for fractal dimension: N(l) ~ l^{-d_B}
        # ln(N(l)) = -d_B * ln(l) + c
        try:
            x_vals = [math.log(lb) for lb in box_sizes if box_counts[box_sizes.index(lb)] > 0]
            y_vals = [math.log(bc) for bc in box_counts if bc > 0]
            
            if len(x_vals) > 1:
                # Basic linear regression
                x_mean = sum(x_vals) / len(x_vals)
                y_mean = sum(y_vals) / len(y_vals)
                
                num = sum((x_vals[i] - x_mean) * (y_vals[i] - y_mean) for i in range(len(x_vals)))
                den = sum((x_vals[i] - x_mean) ** 2 for i in range(len(x_vals)))
                
                if den != 0:
                    slope = num / den
                    return -slope
        except Exception:
            pass
            
        return 1.5  # Fallback empirical estimate for scale-free graphs
