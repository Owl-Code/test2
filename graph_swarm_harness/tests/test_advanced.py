import os
import shutil
import tempfile
import pytest
from unittest.mock import patch, MagicMock

from base_graph.types import ControlMode
from graph_swarm_harness.core.graph_state import SwarmGraphState
from graph_swarm_harness.skills.registry import SkillRegistry
from graph_swarm_harness.tools.core_tool_implementations import web_search_tool, fetch_webpage_content_tool

@pytest.fixture
def temp_skills_dir():
    dirpath = tempfile.mkdtemp()
    
    # Create a mock dynamic skill directory structure
    skill_folder = os.path.join(dirpath, "test_calculator")
    os.makedirs(skill_folder)
    
    skill_md = os.path.join(skill_folder, "SKILL.md")
    with open(skill_md, "w", encoding="utf-8") as f:
        f.write("""---
name: test_calculator
description: "Calculates mathematical values."
when_to_use: "For tests only."
input_schema:
  type: object
  properties:
    x: { type: integer }
  required: [x]
risk_level: LOW
---
Description markup block""")

    run_py = os.path.join(skill_folder, "run.py")
    with open(run_py, "w", encoding="utf-8") as f:
        f.write("result = args.get('x', 0) * 10\n")
        
    yield dirpath
    shutil.rmtree(dirpath)

def test_template_spawn_and_modify():
    swarm = SwarmGraphState(name="template-test")
    # Verify default roles have loaded from roles.yaml
    assert "coordinator" in swarm.role_templates
    assert "coder" in swarm.role_templates
    
    # Spawn coordinator
    coord_id = swarm.spawn_role_agent(role="coordinator")
    agent = swarm.get_agent(coord_id)
    assert agent is not None
    assert agent.role == "coordinator"
    assert "spawn_sub_agent" in agent.active_skills
    assert "create_handoff_edge" in agent.available_tools
    assert agent.beliefs.get("persona") != ""

    # Test dynamic modification
    new_config = {"skills": ["code_execution"], "tools": ["write_file"], "persona": "Test Persona"}
    swarm.update_role_template("coordinator", new_config)
    assert swarm.role_templates["coordinator"]["persona"] == "Test Persona"

def test_dynamic_skill_loading(temp_skills_dir):
    registry = SkillRegistry()
    registry.load_skills_from_directory(temp_skills_dir)
    
    skill = registry.get_skill("test_calculator")
    assert skill is not None
    assert skill.description == "Calculates mathematical values."
    assert skill.risk_level == "LOW"
    
    # Run the dynamic skill code execution wrapper
    run_context = {"swarm": None}
    res = skill.execute(run_context=run_context, x=5)
    assert res == 50

@patch("urllib.request.urlopen")
def test_web_search_tool(mock_urlopen):
    # Mock DDG HTML response
    mock_resp = MagicMock()
    mock_resp.read.return_value = b"""
    <html>
      <a class="result__url" href="http://test.com">Test Title</a>
      <a class="result__snippet" href="http://test.com">This is a test snippet description.</a>
    </html>
    """
    mock_urlopen.return_value.__enter__.return_value = mock_resp
    
    res = web_search_tool("hello", run_context={})
    assert "Test Title" in res
    assert "test snippet description" in res

@patch("urllib.request.urlopen")
def test_fetch_webpage_tool(mock_urlopen):
    mock_resp = MagicMock()
    mock_resp.read.return_value = b"""
    <html>
      <head><title>Test</title></head>
      <body>
        <script>console.log("ignore");</script>
        <style>.ignore {color: red;}</style>
        <p>Main content paragraphs.</p>
        <ul>
          <li>Bullet item list</li>
        </ul>
      </body>
    </html>
    """
    mock_urlopen.return_value.__enter__.return_value = mock_resp
    
    res = fetch_webpage_content_tool("http://test.com", run_context={})
    assert "console.log" not in res
    assert "paragraphs" in res
    assert "- Bullet item list" in res

def test_sqlite_history_db():
    from graph_swarm_harness.harness.persistence_db import SwarmHistoryDB
    from graph_swarm_harness.harness.persistence import checkpoint_to_dict, restore_swarm_from_dict
    
    # Create temp database file
    temp_fd, temp_db = tempfile.mkstemp()
    os.close(temp_fd)
    
    try:
        db = SwarmHistoryDB(db_path=temp_db)
        swarm = SwarmGraphState(name="history-test")
        swarm.spawn_role_agent(role="coordinator")
        
        # Save state at tick 1
        state_dict = checkpoint_to_dict(swarm)
        db.save_checkpoint(tick=1, state_dict=state_dict, emergence=0.75)
        
        # Spawn coder and save at tick 2
        swarm.spawn_role_agent(role="coder")
        state_dict_2 = checkpoint_to_dict(swarm)
        db.save_checkpoint(tick=2, state_dict=state_dict_2, emergence=0.88)
        
        # Verify history retrieval
        history = db.get_history()
        assert len(history) == 2
        assert history[0]["tick"] == 1
        assert history[0]["emergence"] == 0.75
        assert history[1]["tick"] == 2
        assert history[1]["emergence"] == 0.88
        
        # Load tick 1 and verify only coordinator is present
        loaded_1 = db.load_checkpoint(tick=1)
        restored = restore_swarm_from_dict(loaded_1)
        agents = restored.get_agents()
        assert len(agents) == 1
        assert agents[0].role == "coordinator"
    finally:
        try:
            if os.path.exists(temp_db):
                os.remove(temp_db)
        except PermissionError:
            pass

def test_chat_interface():
    from graph_swarm_harness.core.graph_state import SwarmGraphState
    from graph_swarm_harness.tools.core_tool_implementations import reply_to_operator_tool
    
    swarm = SwarmGraphState(name="chat-test")
    # Spawn coordinator
    coord_id = swarm.spawn_role_agent(role="coordinator")
    coordinator = swarm.get_agent(coord_id)
    
    # 1. Simulate sending message from operator to coordinator's inbox
    operator_msg = "Please write a test script."
    coordinator.receive_message(sender_id="operator", message=operator_msg)
    
    assert len(coordinator.inbox) == 1
    assert coordinator.inbox[0]["sender_id"] == "operator"
    assert coordinator.inbox[0]["message"] == operator_msg
    
    # 2. Simulate the coordinator using the reply_to_operator tool
    run_context = {
        "swarm": swarm,
        "agent_id": coord_id
    }
    
    reply_msg = "I will assign the task to coder."
    res = reply_to_operator_tool(message=reply_msg, run_context=run_context)
    
    assert "registered" in res.lower()
    assert len(swarm.chat_replies) == 1
    assert swarm.chat_replies[0]["sender"] == f"{coord_id} (coordinator)"
    assert swarm.chat_replies[0]["text"] == reply_msg

@pytest.mark.asyncio
async def test_goal_deletion_and_async_stepping():
    from graph_swarm_harness.harness.main_loop import SwarmHarnessOrchestrator
    
    orchestrator = SwarmHarnessOrchestrator(config_path="graph_swarm_harness/config.yaml")
    orchestrator.agent_executor.auto_confirm = True
    swarm = orchestrator.setup_swarm(resume=False)
    
    swarm.active_goals = ["Goal A", "Goal B"]
    assert "Goal A" in swarm.active_goals
    swarm.active_goals.remove("Goal A")
    assert "Goal A" not in swarm.active_goals
    assert "Goal B" in swarm.active_goals
    
    # Mock step_agent execution to prevent real network calls
    async def mock_step(swarm, agent_id, tool_registry, skill_registry, workspace_root):
        from base_graph.types import Action, Decision
        return Decision(
            node_id=agent_id,
            selected_action=Action(action_type="idle", parameters={}),
            confidence=0.9,
            reason="Mock Step"
        )
    orchestrator.agent_executor.step_agent = mock_step
    
    # Verify async ticking execution compiles and runs
    await orchestrator.run_tick()

@pytest.mark.asyncio
async def test_agent_permission_gate():
    from unittest.mock import MagicMock
    from graph_swarm_harness.core.graph_state import SwarmGraphState
    from graph_swarm_harness.agents.agent_loop import AgentExecutionLoop
    from graph_swarm_harness.tools.registry import ToolRegistry
    from graph_swarm_harness.skills.registry import SkillRegistry
    
    swarm = SwarmGraphState(name="perm-test")
    # Spawn coder agent
    coder_id = swarm.spawn_role_agent(role="coder")
    coder = swarm.get_agent(coder_id)
    
    # Verify coder does NOT have spawn_sub_agent skill in active_skills
    assert "spawn_sub_agent" not in coder.active_skills
    
    # Try to execute step_agent with a mock LLM response that decided spawn_sub_agent
    loop = AgentExecutionLoop()
    # Mock LLM invocation to return spawn_sub_agent decision
    mock_response = {
        "thought": "I will spawn a sub-agent to delegate tasks.",
        "action": "spawn_sub_agent",
        "args": {"role": "reviewer"},
        "confidence": 0.95,
        "rationale": "Delegation test."
    }
    
    # Wrap the async function mock
    async def mock_invoke(messages, attempts=3):
        return mock_response
    loop._invoke_llm_with_repair = mock_invoke
    
    tool_reg = ToolRegistry()
    skill_reg = SkillRegistry()
    
    # Let's register spawn_sub_agent in global skill registry
    from graph_swarm_harness.skills.core_skill_implementations import setup_core_skills
    setup_core_skills(skill_reg)
    
    decision = await loop.step_agent(
        swarm=swarm,
        agent_id=coder_id,
        tool_registry=tool_reg,
        skill_registry=skill_reg,
        workspace_root="."
    )
    
    # Check that decision returned idle and recorded permission denial
    assert decision.selected_action.action_type == "idle"
    assert "not in your allowed" in decision.reason

def test_dynamic_create_new_role_tool():
    from graph_swarm_harness.core.graph_state import SwarmGraphState
    from graph_swarm_harness.tools.core_tool_implementations import create_new_role_tool
    
    swarm = SwarmGraphState(name="role-create-test")
    run_context = {
        "swarm": swarm,
        "agent_id": "operator"
    }
    
    # Create new role configuration
    res = create_new_role_tool(
        role_name="tester",
        skills=["file_io"],
        tools=["read_file"],
        persona="Tester persona instructions.",
        run_context=run_context
    )
    
    assert "successfully created" in res.lower()
    assert "tester" in swarm.role_templates
    assert swarm.role_templates["tester"]["skills"] == ["file_io"]
    assert swarm.role_templates["tester"]["tools"] == ["read_file"]
    assert swarm.role_templates["tester"]["persona"] == "Tester persona instructions."

@pytest.mark.asyncio
async def test_inactive_agent_memory_clearing():
    from graph_swarm_harness.harness.main_loop import SwarmHarnessOrchestrator
    
    orchestrator = SwarmHarnessOrchestrator(config_path="graph_swarm_harness/config.yaml")
    orchestrator.agent_executor.auto_confirm = True
    swarm = orchestrator.setup_swarm(resume=False)
    
    # Fetch coordinator and coder agents
    coord_id = [a.id for a in swarm.get_agents() if a.role == "coordinator"][0]
    coder_id = [a.id for a in swarm.get_agents() if a.role == "coder"][0]
    
    coder_agent = swarm.get_agent(coder_id)
    coder_agent.node.local_memory["last_thought"] = "Old coder thought"
    coder_agent.node.local_memory["last_decision_reason"] = "Old coder reason"
    
    # Force only coordinator to be active this tick by mocking select_active_agents
    orchestrator.select_active_agents = lambda: [coord_id]
    
    # Mock step_agent execution to prevent real network calls
    async def mock_step(swarm, agent_id, tool_registry, skill_registry, workspace_root):
        from base_graph.types import Action, Decision
        return Decision(
            node_id=agent_id,
            selected_action=Action(action_type="idle", parameters={}),
            confidence=0.9,
            reason="Mock Step"
        )
    orchestrator.agent_executor.step_agent = mock_step
    
    await orchestrator.run_tick()
    
    # Assert coder node's memory details were cleared/reset
    assert coder_agent.node.local_memory["last_thought"] == "Resting/Conserving state"
    assert "Agent inactive this tick" in coder_agent.node.local_memory["last_decision_reason"]

@pytest.mark.asyncio
async def test_objective_energy_harvesting():
    from graph_swarm_harness.core.graph_state import SwarmGraphState
    from graph_swarm_harness.agents.agent_loop import AgentExecutionLoop
    from graph_swarm_harness.tools.registry import ToolRegistry
    from graph_swarm_harness.skills.registry import SkillRegistry
    
    swarm = SwarmGraphState(name="harvest-test")
    coord_id = swarm.spawn_role_agent(role="coordinator")
    coordinator = swarm.get_agent(coord_id)
    
    swarm.active_goals = ["Test Goal"]
    swarm.goal_energy = {"Test Goal": 100.0}
    coordinator.energy = 50.0
    
    loop = AgentExecutionLoop()
    mock_response = {
        "thought": "I will query the graph to understand our swarm topology.",
        "action": "graph_query",
        "args": {},
        "confidence": 0.95,
        "rationale": "Productive task."
    }
    
    async def mock_invoke(messages, attempts=3):
        return mock_response
    loop._invoke_llm_with_repair = mock_invoke
    
    from graph_swarm_harness.skills.core_skill_implementations import setup_core_skills
    tool_reg = ToolRegistry()
    skill_reg = SkillRegistry()
    setup_core_skills(skill_reg)
    
    await loop.step_agent(
        swarm=swarm,
        agent_id=coord_id,
        tool_registry=tool_reg,
        skill_registry=skill_reg,
        workspace_root="."
    )
    
    # Verify goal energy was drained by 10.0
    assert swarm.goal_energy["Test Goal"] == 90.0
    
    # Verify agent energy was recharged (50.0 - 2.5 metabolic decay cost + 15.0 harvest = 62.5)
    assert coordinator.energy == 62.5
    
    # Verify stigmergic signal "task_crumb" is deposited on the node
    deposits = coordinator.node.local_memory.get("stigmergy_deposits", [])
    assert any(d["signal"] == "task_crumb" for d in deposits)
