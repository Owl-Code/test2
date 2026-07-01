import pytest
from base_graph import HybridControlSwarmGraph, EmergenceNode, AdaptiveEdge, ControlMode, TrophallaxisEdge

@pytest.fixture
def empty_swarm():
    return HybridControlSwarmGraph(name="test-swarm-empty", seed=42)

@pytest.fixture
def small_swarm():
    swarm = HybridControlSwarmGraph(name="test-swarm-small", seed=42)
    # Add nodes
    n1 = EmergenceNode(id="node_a", resources={"energy": 100.0}, opinions={"topic": 0.5})
    n2 = EmergenceNode(id="node_b", resources={"energy": 50.0}, opinions={"topic": -0.5})
    swarm.graph.add_node(n1)
    swarm.graph.add_node(n2)
    # Add communication edge
    edge = AdaptiveEdge(source_id="node_a", target_id="node_b", weight=1.0)
    swarm.graph.add_edge(edge)
    return swarm

@pytest.fixture
def trophallaxis_swarm():
    swarm = HybridControlSwarmGraph(name="test-swarm-trophallaxis", seed=42)
    n1 = EmergenceNode(id="node_a", resources={"energy": 100.0})
    n2 = EmergenceNode(id="node_b", resources={"energy": 10.0}) # starving
    swarm.graph.add_node(n1)
    swarm.graph.add_node(n2)
    edge = TrophallaxisEdge(source_id="node_a", target_id="node_b", weight=1.0)
    swarm.graph.add_edge(edge)
    return swarm
