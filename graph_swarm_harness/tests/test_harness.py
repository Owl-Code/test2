import os
import shutil
import tempfile
import pytest

from base_graph.types import ControlMode, Action
from graph_swarm_harness.core.graph_state import SwarmGraphState
from graph_swarm_harness.core.hybrid_control import HybridControlManager
from graph_swarm_harness.tools.registry import ToolRegistry
from graph_swarm_harness.tools.core_tool_implementations import setup_core_tools
from graph_swarm_harness.skills.registry import SkillRegistry
from graph_swarm_harness.skills.core_skill_implementations import setup_core_skills
from graph_swarm_harness.harness.persistence import save_swarm_state, load_swarm_state

@pytest.fixture
def temp_workspace():
    dirpath = tempfile.mkdtemp()
    yield dirpath
    shutil.rmtree(dirpath)

def test_registry_registration():
    t_reg = ToolRegistry()
    setup_core_tools(t_reg)
    assert len(t_reg.list_tools()) > 0
    assert t_reg.get_tool("read_file") is not None
    assert t_reg.get_tool("invalid_tool_name") is None

    s_reg = SkillRegistry()
    setup_core_skills(s_reg)
    assert len(s_reg.list_skills()) > 0
    assert s_reg.get_skill("code_execution") is not None

def test_dynamic_agent_spawning():
    swarm = SwarmGraphState(name="test-swarm")
    assert len(swarm.get_agents()) == 0
    
    agent_id = swarm.spawn_dynamic_agent(
        role="coder",
        initial_skills=["code_execution"],
        initial_tools=["read_file", "write_file"]
    )
    
    assert len(swarm.get_agents()) == 1
    agent = swarm.get_agent(agent_id)
    assert agent is not None
    assert agent.role == "coder"
    assert "code_execution" in agent.active_skills
    assert "read_file" in agent.available_tools

    # Test hibernate/kill
    swarm.hibernate_or_kill_agent(agent_id, reason="testing shutdown")
    assert len(swarm.get_agents()) == 0

def test_persistence_and_integrity(temp_workspace):
    swarm = SwarmGraphState(name="persisted-swarm")
    swarm.spawn_dynamic_agent(
        role="coordinator",
        initial_skills=["graph_query"],
        initial_tools=["query_swarm_emergence"]
    )
    
    # Save checkpoint
    saved_file = save_swarm_state(swarm, temp_workspace)
    assert os.path.exists(saved_file)
    
    # Restore checkpoint
    restored_swarm = load_swarm_state(saved_file)
    assert restored_swarm.name == "persisted-swarm"
    assert len(restored_swarm.get_agents()) == 1
    assert restored_swarm.get_agents()[0].role == "coordinator"
    assert restored_swarm.provenance.verify_chain() is True

def test_control_manager_adaptation():
    swarm = SwarmGraphState(name="adaptive-swarm")
    agent_id = swarm.spawn_dynamic_agent(
        role="worker",
        initial_skills=[],
        initial_tools=[]
    )
    
    manager = HybridControlManager()
    agent = swarm.get_agent(agent_id)
    
    # Simulate high starvation (force HIERARCHICAL)
    agent.energy = 10.0
    health = swarm.compute_swarm_health()
    new_mode = manager.evaluate_and_adapt(swarm, health)
    
    assert new_mode == "HIERARCHICAL"
    assert agent.node.control_mode == ControlMode.HIERARCHICAL
