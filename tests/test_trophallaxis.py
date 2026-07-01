import logging
import pytest
from base_graph import EmergenceNode, TrophallaxisEdge, HybridControlSwarmGraph, ControlMode

logger = logging.getLogger(__name__)

def test_trophallaxis_transfer(trophallaxis_swarm):
    logger.info("Starting test_trophallaxis_transfer")
    node_a = trophallaxis_swarm.graph.nodes["node_a"]
    node_b = trophallaxis_swarm.graph.nodes["node_b"]
    
    assert node_b.resources["energy"] == 10.0 # starving
    logger.info(f"Initial states - node_a: {node_a.resources['energy']}, node_b: {node_b.resources['energy']}")
    
    # Configure safety parameters
    trophallaxis_swarm.trophallaxis.safety_threshold = 20.0
    trophallaxis_swarm.trophallaxis.sharing_rate = 0.2
    
    # Distribute resources
    logger.info("Executing distribute_resources on trophallaxis swarm")
    transfers = trophallaxis_swarm.trophallaxis.distribute_resources(trophallaxis_swarm.graph)
    assert transfers == 1
    
    logger.info(f"Final states - node_a: {node_a.resources['energy']}, node_b: {node_b.resources['energy']}")
    assert abs(node_b.resources["energy"] - 28.0) < 1e-3
    assert abs(node_a.resources["energy"] - 82.0) < 1e-3
    logger.info("Trophallaxis transfer test passed successfully")

def test_trophallaxis_safety_block():
    logger.info("Starting test_trophallaxis_safety_block")
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
    logger.info("Executing distribute_resources with safety thresholds configured")
    transfers = swarm.trophallaxis.distribute_resources(swarm.graph)
    assert transfers == 1
    
    logger.info(f"Final states under safety block - node_a: {n1.resources['energy']}, node_b: {n2.resources['energy']}")
    assert abs(n1.resources["energy"] - 20.0) < 1e-3
    assert abs(n2.resources["energy"] - 15.0) < 1e-3
    logger.info("Safety block capped transfer as expected")

def test_metabolic_decay(trophallaxis_swarm):
    logger.info("Starting test_metabolic_decay")
    # Simulating metabolism cost = 5.0
    logger.info("Simulating metabolic decay with cost = 5.0")
    starving = trophallaxis_swarm.trophallaxis.simulate_metabolism(trophallaxis_swarm.graph, cost=5.0)
    
    assert len(starving) == 1 # Only node_b is under safety_threshold (10.0 -> 5.0)
    assert starving[0]["node_id"] == "node_b"
    assert starving[0]["current_level"] == 5.0
    assert trophallaxis_swarm.graph.nodes["node_a"].resources["energy"] == 95.0
    logger.info("Metabolic decay verified; starvation detected correctly")
