import math
from typing import Any, Dict, List, Set
from base_graph.primitives.graph import BaseGraph
from base_graph.primitives.subgraph import DiffusionTrajectory
from base_graph.primitives.node import EmergenceNode
from base_graph.utils.math import get_eigenvalues, compute_entropy

def spectral_gap(graph: BaseGraph) -> float:
    """Computes the spectral gap (second smallest eigenvalue of the normalized Laplacian).
    
    A higher value indicates stronger connectivity and faster synchronization potential.
    """
    n = len(graph.nodes)
    if n <= 1:
        return 0.0
        
    L = graph.laplacian_matrix(normalized=True)
    
    # Extract eigenvalues
    eigenvals = get_eigenvalues(L)
    if len(eigenvals) < 2:
        return 0.0
        
    # Sorted ascending
    eigenvals.sort()
    
    # Return the second eigenvalue (lambda_2)
    # Due to floating point noise, lambda_1 might not be exactly 0, so we take the second element.
    return float(eigenvals[1])

def graph_diffusion_entropy(trajectory: DiffusionTrajectory) -> float:
    """Returns the final entropy of the state diffusion process."""
    if not trajectory.entropy_curve:
        return 1.0
    return trajectory.entropy_curve[-1]

def emergence_level(graph: BaseGraph, history: List[Dict[str, Any]]) -> float:
    """Calculates the composite emergence level E in [0, 1].
    
    Formula:
      E = 0.4 * spectral_gap_norm + 0.3 * entropy_reduction + 0.3 * stability
    """
    n = len(graph.nodes)
    if n <= 1:
        return 0.0

    # 1. Connectivity factor (spectral gap normalized to max of 1.0)
    gap = spectral_gap(graph)
    spectral_gap_norm = min(1.0, max(0.0, gap))

    # 2. Cohesion/Order factor (1 - normalized entropy of opinions/resources)
    # Let's extract opinions if available, else energy resources
    values = []
    has_opinions = False
    
    for node in graph.nodes.values():
        if isinstance(node, EmergenceNode):
            if node.opinions:
                has_opinions = True
                values.append(sum(node.opinions.values()) / len(node.opinions))
            else:
                values.append(node.resources.get("energy", 0.0))
        else:
            values.append(node.state.get("opinion", node.state.get("energy", 0.0)))

    # Compute shannon entropy
    if has_opinions:
        # Scale to positive range for entropy
        min_v = min(values) if values else 0.0
        if min_v < 0:
            pos_values = [v - min_v for v in values]
        else:
            pos_values = values
    else:
        pos_values = [max(0.0, v) for v in values]
        
    entropy = compute_entropy(pos_values)
    max_entropy = math.log2(n) if n > 1 else 1.0
    norm_entropy = entropy / max_entropy if max_entropy > 0 else 1.0
    entropy_reduction = 1.0 - norm_entropy

    # 3. Stability factor (temporal consistency of node states over history)
    stability = 0.5
    if len(history) > 2:
        # Variance of the mean values over the last few history steps
        last_steps = history[-5:]
        mean_energies = []
        for step in last_steps:
            nodes_data = step.get("nodes", [])
            energies = []
            for nd in nodes_data:
                # nodes in history can be serialized dicts
                res = nd.get("resources", {})
                energies.append(res.get("energy", 0.0))
            if energies:
                mean_energies.append(sum(energies) / len(energies))
                
        if len(mean_energies) > 1:
            mean_of_means = sum(mean_energies) / len(mean_energies)
            variance = sum((m - mean_of_means) ** 2 for m in mean_energies) / len(mean_energies)
            # High stability = low variance in average energy/opinion level
            stability = 1.0 / (1.0 + variance)

    composite = 0.4 * spectral_gap_norm + 0.3 * entropy_reduction + 0.3 * stability
    return min(1.0, max(0.0, composite))

def swarm_antifragility_index(graph: BaseGraph) -> float:
    """Calculates an index of structural adaptation.
    
    Measures how much edge strengths have increased relative to base weights under usage/stress.
    """
    if not graph.edges:
        return 0.0
        
    total_strength_delta = 0.0
    for edge in graph.edges.values():
        total_strength_delta += max(0.0, edge.strength - 1.0)
        
    mean_adaptation = total_strength_delta / len(graph.edges)
    # Scale to standard index range [0, 1] using soft saturation
    return mean_adaptation / (1.0 + mean_adaptation)

def estimate_betti_numbers(graph: BaseGraph) -> Dict[str, int]:
    """Estimates Betti numbers B0 (connected components) and B1 (1D cycles) of the network.
    
    To run rigorous persistent homology, integrate libraries like 'gudhi' or 'ripser':
    
    Example:
      import ripser
      import numpy as np
      # compute distance matrix
      dm = get_distance_matrix(graph)
      result = ripser.ripser(dm, distance_matrix=True)
      # Betti numbers are counts of birth-death bars in result['dgms']
    """
    # B0 estimation: connected components using BFS/DFS
    visited: Set[str] = set()
    b0 = 0
    for node_id in graph.nodes.keys():
        if node_id not in visited:
            b0 += 1
            # Run BFS to cover component
            queue = [node_id]
            while queue:
                curr = queue.pop(0)
                if curr not in visited:
                    visited.add(curr)
                    # Add neighbors (treat undirected)
                    for edge in graph.edges.values():
                        if edge.source_id == curr and edge.target_id not in visited:
                            queue.append(edge.target_id)
                        elif edge.target_id == curr and edge.source_id not in visited:
                            queue.append(edge.source_id)
                            
    # B1 estimation: simple cycle estimation using Euler Characteristic for planar-like graphs:
    # V - E + F = 1 + B1 - B0  -> B1 = E - V + B0 for undirected trees/forests.
    # We estimate B1 as E - V + B0 (clamped to >= 0)
    v = len(graph.nodes)
    # Unduplicated undirected edges count
    undirected_edges = set()
    for edge in graph.edges.values():
        key = tuple(sorted([edge.source_id, edge.target_id]))
        undirected_edges.add(key)
        
    e = len(undirected_edges)
    b1 = max(0, e - v + b0)
    
    return {
        "B0": b0,
        "B1": b1
    }
