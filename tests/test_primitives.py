import pytest
from base_graph import BaseNode, EmergenceNode, AdaptiveEdge, BaseGraph, ControlMode, EdgeType

def test_base_node_creation():
    node = BaseNode(id="node_1", state={"key": "val"}, metadata={"meta": 1})
    assert str(node.id) == "node_1"
    assert node.state["key"] == "val"
    assert node.metadata["meta"] == 1

def test_emergence_node_initialization():
    node = EmergenceNode(id="node_e")
    assert node.resources["energy"] == 100.0
    assert node.control_mode == ControlMode.EMERGENCE
    assert len(node.opinions) == 0

def test_adaptive_edge_updates():
    edge = AdaptiveEdge(source_id="node_a", target_id="node_b", weight=1.0)
    assert edge.id == "node_a->node_b"
    assert edge.strength == 1.0
    
    # Update weight
    edge.update_weight(delta=0.5, reason="test_reinforce")
    assert edge.weight == 1.5
    assert edge.strength > 1.0
    assert edge.usage_count == 1

def test_base_graph_add_remove():
    graph = BaseGraph()
    n1 = BaseNode(id="a")
    n2 = BaseNode(id="b")
    graph.add_node(n1)
    graph.add_node(n2)
    
    assert len(graph.nodes) == 2
    
    edge = AdaptiveEdge(source_id="a", target_id="b")
    graph.add_edge(edge)
    assert len(graph.edges) == 1
    
    neighbors = graph.get_neighbors("a")
    assert len(neighbors) == 1
    assert neighbors[0].id == "b"
    
    # Remove node
    graph.remove_node("b")
    assert len(graph.nodes) == 1
    assert len(graph.edges) == 0
    assert len(graph.get_neighbors("a")) == 0

def test_laplacian_calculation():
    graph = BaseGraph()
    graph.add_node(BaseNode(id="a"))
    graph.add_node(BaseNode(id="b"))
    edge = AdaptiveEdge(source_id="a", target_id="b", weight=1.0)
    graph.add_edge(edge)
    
    # normalized Laplacian L of symmetric 2-node graph:
    # A = [[0, 1], [1, 0]]
    # D = [[1, 0], [0, 1]]
    # L = I - D^{-1/2} A D^{-1/2} = [[1, -1], [-1, 1]]
    L = graph.laplacian_matrix(normalized=True)
    # Check shape/values
    assert len(L) == 2
    assert abs(L[0][0] - 1.0) < 1e-9
    assert abs(L[0][1] - (-1.0)) < 1e-9
