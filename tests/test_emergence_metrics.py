import pytest
from base_graph import BaseGraph, BaseNode, AdaptiveEdge
from base_graph.core.metrics import (
    spectral_gap,
    emergence_level,
    swarm_antifragility_index,
    estimate_betti_numbers
)
from base_graph.utils.math import compute_entropy

def test_spectral_gap_clique():
    graph = BaseGraph()
    # Create complete graph of 3 nodes (K3 triangle)
    graph.add_node(BaseNode(id="a"))
    graph.add_node(BaseNode(id="b"))
    graph.add_node(BaseNode(id="c"))
    
    graph.add_edge(AdaptiveEdge(source_id="a", target_id="b"))
    graph.add_edge(AdaptiveEdge(source_id="b", target_id="c"))
    graph.add_edge(AdaptiveEdge(source_id="c", target_id="a"))
    
    # Normalized Laplacian of K3 eigenvalues are: 0, 1.5, 1.5
    # So spectral gap should be 1.5
    gap = spectral_gap(graph)
    assert abs(gap - 1.5) < 1e-3

def test_entropy_calculation():
    # Equal probability
    entropy = compute_entropy([10.0, 10.0, 10.0, 10.0])
    # H = - 4 * (0.25 * log2(0.25)) = -4 * 0.25 * (-2) = 2.0
    assert abs(entropy - 2.0) < 1e-9
    
    # Uniform 0
    assert compute_entropy([0.0, 0.0]) == 0.0

def test_antifragility_score():
    graph = BaseGraph()
    graph.add_node(BaseNode(id="a"))
    graph.add_node(BaseNode(id="b"))
    edge = AdaptiveEdge(source_id="a", target_id="b")
    graph.add_edge(edge)
    
    # No usage -> antifragility index 0
    assert swarm_antifragility_index(graph) == 0.0
    
    # Update edge weight (increases strength)
    edge.update_weight(delta=2.0, reason="test")
    score = swarm_antifragility_index(graph)
    assert score > 0.0
    assert score < 1.0

def test_betti_estimation():
    # Simple line: A - B
    graph = BaseGraph()
    graph.add_node(BaseNode(id="a"))
    graph.add_node(BaseNode(id="b"))
    graph.add_edge(AdaptiveEdge(source_id="a", target_id="b"))
    
    betti = estimate_betti_numbers(graph)
    assert betti["B0"] == 1  # 1 connected component
    assert betti["B1"] == 0  # 0 cycles
    
    # Simple triangle cycle
    graph.add_node(BaseNode(id="c"))
    graph.add_edge(AdaptiveEdge(source_id="b", target_id="c"))
    graph.add_edge(AdaptiveEdge(source_id="c", target_id="a"))
    
    betti_cycle = estimate_betti_numbers(graph)
    assert betti_cycle["B0"] == 1
    assert betti_cycle["B1"] == 1  # 1 cycle formed
