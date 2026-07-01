import pytest
from base_graph import HybridControlSwarmGraph, EmergenceNode, AdaptiveEdge, ControlMode

def test_opinion_dynamics_diffusion(small_swarm):
    # Retrieve diffusion subgraph
    traj = small_swarm.diffusion_subgraph.run_diffusion(
        model="opinion",
        steps=10,
        params={"epsilon": 1.1, "topic": "topic"}
    )
    
    assert traj.model == "opinion"
    assert len(traj.history) > 1
    # Check that opinions converged closer to each other
    final_a = traj.final_state["node_a"]["topic"]
    final_b = traj.final_state["node_b"]["topic"]
    assert abs(final_a - final_b) < 0.2

def test_heat_diffusion(small_swarm):
    # Heat diffusion on small swarm energy resources
    # Initial: a=100.0, b=50.0. After heat, energy should equalize
    traj = small_swarm.diffusion_subgraph.run_diffusion(
        model="heat",
        steps=5,
        params={"alpha": 0.2, "resource": "energy"}
    )
    
    assert traj.model == "heat"
    final_a = traj.final_state["node_a"]["energy"]
    final_b = traj.final_state["node_b"]["energy"]
    
    # Conservation of total energy (150.0 total)
    assert abs((final_a + final_b) - 150.0) < 1e-3
    # Check that energy moved from rich (a) to poor (b)
    assert final_a < 100.0
    assert final_b > 50.0

def test_sir_diffusion(small_swarm):
    # Set statuses to susceptible (0.0) except node_a is infected (1.0)
    small_swarm.graph.nodes["node_a"].state["sir_status"] = 1.0
    small_swarm.graph.nodes["node_b"].state["sir_status"] = 0.0
    
    traj = small_swarm.diffusion_subgraph.run_diffusion(
        model="sir",
        steps=10,
        params={"beta": 1.0, "gamma": 0.0, "seed": 42} # deterministic infection, no recovery
    )
    
    assert traj.model == "sir"
    # Node B must have gotten infected
    assert traj.final_state["node_b"]["sir"] == 1.0

def test_dynamic_restructure():
    swarm = HybridControlSwarmGraph()
    swarm.graph.add_node(EmergenceNode(id="a"))
    swarm.graph.add_node(EmergenceNode(id="b"))
    swarm.graph.add_node(EmergenceNode(id="c"))
    
    # Add strong and weak edge
    swarm.graph.add_edge(AdaptiveEdge(source_id="a", target_id="b", weight=5.0))
    swarm.graph.add_edge(AdaptiveEdge(source_id="b", target_id="c", weight=0.1)) # weak
    
    # Restructure: prune edges < 0.5 weight
    swarm.graph.dynamic_restructure({"prune_weak_edges": 0.5})
    
    assert "a->b" in swarm.graph.edges
    assert "b->c" not in swarm.graph.edges
