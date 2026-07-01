import logging
import pytest
from base_graph import BaseNode, EmergenceNode, AdaptiveEdge, BaseGraph, ControlMode, EdgeType

logger = logging.getLogger(__name__)

def test_base_node_creation():
    logger.info("Initializing base node with ID 'node_1'")
    node = BaseNode(id="node_1", state={"key": "val"}, metadata={"meta": 1})
    assert str(node.id) == "node_1"
    assert node.state["key"] == "val"
    assert node.metadata["meta"] == 1
    logger.info("Base node assertions verified successfully")

def test_emergence_node_initialization():
    logger.info("Initializing emergence node with ID 'node_e'")
    node = EmergenceNode(id="node_e")
    assert node.resources["energy"] == 100.0
    assert node.control_mode == ControlMode.EMERGENCE
    assert len(node.opinions) == 0
    logger.info("Emergence node initial attributes verified")

def test_adaptive_edge_updates():
    logger.info("Initializing adaptive edge node_a -> node_b")
    edge = AdaptiveEdge(source_id="node_a", target_id="node_b", weight=1.0)
    assert edge.id == "node_a->node_b"
    assert edge.strength == 1.0
    
    logger.info("Updating weight on edge with delta 0.5")
    edge.update_weight(delta=0.5, reason="test_reinforce")
    assert edge.weight == 1.5
    assert edge.strength > 1.0
    assert edge.usage_count == 1
    logger.info("Adaptive edge update metrics verified")

def test_base_graph_add_remove():
    logger.info("Creating new BaseGraph instance")
    graph = BaseGraph()
    n1 = BaseNode(id="a")
    n2 = BaseNode(id="b")
    graph.add_node(n1)
    graph.add_node(n2)
    
    assert len(graph.nodes) == 2
    logger.info("Added 2 nodes to the graph")
    
    edge = AdaptiveEdge(source_id="a", target_id="b")
    graph.add_edge(edge)
    assert len(graph.edges) == 1
    logger.info("Added edge a -> b to the graph")
    
    neighbors = graph.get_neighbors("a")
    assert len(neighbors) == 1
    assert neighbors[0].id == "b"
    
    logger.info("Removing node 'b' and verifying edge cleanup")
    graph.remove_node("b")
    assert len(graph.nodes) == 1
    assert len(graph.edges) == 0
    assert len(graph.get_neighbors("a")) == 0
    logger.info("Graph structural changes verified successfully")

def test_laplacian_calculation():
    logger.info("Creating graph for Laplacian matrix calculations")
    graph = BaseGraph()
    graph.add_node(BaseNode(id="a"))
    graph.add_node(BaseNode(id="b"))
    edge = AdaptiveEdge(source_id="a", target_id="b", weight=1.0)
    graph.add_edge(edge)
    
    logger.info("Computing normalized Laplacian matrix")
    L = graph.laplacian_matrix(normalized=True)
    assert len(L) == 2
    assert abs(L[0][0] - 1.0) < 1e-9
    assert abs(L[0][1] - (-1.0)) < 1e-9
    logger.info("Laplacian eigenvalues/entries verified")
