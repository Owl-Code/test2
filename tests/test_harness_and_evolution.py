import pytest
from base_graph.core.simulation_harness import SimulationHarness
from base_graph.core.meta_evolver import MetaSkillEvolver

def test_simulation_harness_local_execution():
    harness = SimulationHarness()
    
    # Setup ring trial
    swarm = harness.setup_trial(name="test-trial", num_nodes=4, topology="ring")
    assert len(swarm.graph.nodes) == 4
    
    # Run 3 steps using cooperative strategy parameters
    strategy = {
        "sharing_rate": 0.25,
        "safety_threshold": 20.0,
        "cooperation_weight": 0.8,
        "consensus_weight": 0.2
    }
    report = harness.run_trial(steps=3, strategy=strategy)
    
    # Check output properties
    assert report["step_count"] == 3
    assert report["final_emergence"] >= 0.0
    assert report["final_energy_avg"] > 0.0
    assert report["provenance_valid"] is True

def test_evolver_mutation_bounds():
    evolver = MetaSkillEvolver()
    
    # Generate candidate
    cand = evolver.create_random_candidate()
    assert "sharing_rate" in cand
    assert 0.05 <= cand["sharing_rate"] <= 0.40
    
    # Mutate multiple times to ensure boundaries are capped
    for _ in range(20):
        cand = evolver.mutate(cand)
        assert 0.05 <= cand["sharing_rate"] <= 0.50
        assert 10.0 <= cand["safety_threshold"] <= 40.0
        assert 0.0 <= cand["cooperation_weight"] <= 1.0
        assert 0.0 <= cand["consensus_weight"] <= 1.0
        assert cand["fitness"] == 0.0

def test_evolution_loop_one_generation():
    evolver = MetaSkillEvolver()
    
    # Run a quick 1-generation optimization of 2 candidates
    best = evolver.run_evolution(generations=1, population_size=2, steps_per_trial=2)
    
    assert best["fitness"] >= 0.0
    assert "sharing_rate" in best
    assert "cooperation_weight" in best
