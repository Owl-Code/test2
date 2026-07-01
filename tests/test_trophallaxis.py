import pytest
from base_graph import EmergenceNode, TrophallaxisEdge, HybridControlSwarmGraph, ControlMode

def test_trophallaxis_transfer(trophallaxis_swarm):
    node_a = trophallaxis_swarm.graph.nodes["node_a"]
    node_b = trophallaxis_swarm.graph.nodes["node_b"]
    
    assert node_b.resources["energy"] == 10.0 # starving
    
    # Configure safety parameters
    trophallaxis_swarm.trophallaxis.safety_threshold = 20.0
    trophallaxis_swarm.trophallaxis.sharing_rate = 0.2
    
    # Distribute resources
    transfers = trophallaxis_swarm.trophallaxis.distribute_resources(trophallaxis_swarm.graph)
    assert transfers == 1
    
    # Node B received resource. Node A transferred part of surplus:
    # A initial: 100.0, B initial: 10.0. Difference: 90.0.
    # Flow amount: 0.2 * 90 = 18.0.
    # B final should be: 10.0 + 18.0 = 28.0.
    # A final should be: 100.0 - 18.0 = 82.0.
    assert abs(node_b.resources["energy"] - 28.0) < 1e-3
    assert abs(node_a.resources["energy"] - 82.0) < 1e-3

def test_trophallaxis_safety_block():
    swarm = HybridControlSwarmGraph()
    n1 = EmergenceNode(id="node_a", resources={"energy": 25.0}) # near threshold (20.0)
    n2 = EmergenceNode(id="node_b", resources={"energy": 10.0})
    swarm.graph.add_node(n1)
    swarm.graph.add_node(n2)
    edge = TrophallaxisEdge(source_id="node_a", target_id="node_b")
    swarm.graph.add_edge(edge)
    
    swarm.trophallaxis.safety_threshold = 20.0
    swarm.trophallaxis.sharing_rate = 0.5 # would try to transfer 7.5
    
    # Distribute
    transfers = swarm.trophallaxis.distribute_resources(swarm.graph)
    assert transfers == 1
    
    # Node A had 25.0. It can only transfer up to 5.0 (25.0 - 20.0 safety threshold)
    # So transfer was capped to 5.0
    assert abs(n1.resources["energy"] - 20.0) < 1e-3
    assert abs(n2.resources["energy"] - 15.0) < 1e-3

def test_metabolic_decay(trophallaxis_swarm):
    # Simulating metabolism cost = 5.0
    starving = trophallaxis_swarm.trophallaxis.simulate_metabolism(trophallaxis_swarm.graph, cost=5.0)
    
    assert len(starving) == 1 # Only node_b is under safety_threshold (10.0 -> 5.0)
    assert starving[0]["node_id"] == "node_b"
    assert starving[0]["current_level"] == 5.0
    assert trophallaxis_swarm.graph.nodes["node_a"].resources["energy"] == 95.0
