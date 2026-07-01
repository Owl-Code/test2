import pytest
from base_graph import HybridControlSwarmGraph, EmergenceNode, ControlMode
from base_graph.core.provenance import ProvenanceChain

def test_provenance_chain_mutations():
    chain = ProvenanceChain()
    assert chain.verify_chain() is True
    
    # Add mutations
    chain.add_mutation("user", "create_node", "node_1", before=None, after={"id": "node_1"})
    assert len(chain.chain) == 1
    assert chain.verify_chain() is True
    
    chain.add_mutation("user", "update_resource", "node_1", before={"energy": 100}, after={"energy": 50})
    assert len(chain.chain) == 2
    assert chain.verify_chain() is True

def test_corrupt_provenance_fails():
    chain = ProvenanceChain()
    chain.add_mutation("user", "op1", "node_1", None, {"id": 1})
    chain.add_mutation("user", "op2", "node_1", {"id": 1}, {"id": 2})
    
    # Tamper with block
    chain.chain[0].delta.actor = "malicious_actor"
    # Re-verifying should now detect mismatch
    assert chain.verify_chain() is False

def test_checkpoint_and_restore(small_swarm):
    # Retrieve initial checkpoint
    chk = small_swarm.checkpoint()
    assert chk.state_hash is not None
    
    # Modify graph states
    small_swarm.graph.nodes["node_a"].resources["energy"] = 12.0
    small_swarm.graph.nodes["node_b"].control_mode = ControlMode.STIGMERGIC
    
    # Restore back to check point
    small_swarm.restore(chk)
    
    # Check that initial states are recovered
    assert small_swarm.graph.nodes["node_a"].resources["energy"] == 100.0
    assert small_swarm.graph.nodes["node_b"].control_mode == ControlMode.EMERGENCE
    # Check state integrity
    assert small_swarm.provenance.verify_chain() is True
