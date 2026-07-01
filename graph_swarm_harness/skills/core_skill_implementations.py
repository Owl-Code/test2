from typing import Dict, Any, List, Optional
from base_graph.primitives.edge import TrophallaxisEdge
from base_graph.types import ControlMode
from graph_swarm_harness.skills.registry import SkillRegistry
from graph_swarm_harness.tools.core_tool_implementations import (
    read_file_tool,
    write_file_tool,
    execute_python_snippet_tool,
    create_handoff_edge_tool,
    update_swarm_node_state_tool
)

def code_execution_skill(code: str, run_context: Dict[str, Any]) -> str:
    """Orchestrates writing a temporary script, executing it, and reporting outputs."""
    return execute_python_snippet_tool(code, run_context)

def file_io_skill(operation: str, path: str, content: str = "", run_context: Dict[str, Any] = None) -> str:
    """Orchestrates safe reading or writing files in the workspace."""
    run_context = run_context or {}
    if operation.lower() == "read":
        return read_file_tool(path, run_context)
    elif operation.lower() == "write":
        return write_file_tool(path, content, run_context)
    else:
        return f"Error: Unknown file operation '{operation}'. Use 'read' or 'write'."

def graph_query_skill(run_context: Dict[str, Any]) -> Dict[str, Any]:
    """Queries details about the graph nodes and edges."""
    swarm = run_context["swarm"]
    agents = []
    for a in swarm.get_agents():
        agents.append({
            "id": a.id,
            "role": a.role,
            "energy": a.energy,
            "active_skills": a.active_skills,
            "available_tools": a.available_tools,
            "control_mode": a.node.control_mode.value,
            "beliefs": a.beliefs,
            "inbox_size": len(a.inbox)
        })
    
    edges = []
    for eid, e in swarm.graph.edges.items():
        edges.append({
            "id": e.id,
            "weight": e.weight,
            "strength": e.strength,
            "type": e.edge_type.value
        })
        
    return {
        "agents": agents,
        "edges": edges,
        "global_mode": swarm.get_agents()[0].node.control_mode.value if agents else "UNKNOWN"
    }

def graph_update_skill(node_id: str, updates: Dict[str, Any], run_context: Dict[str, Any]) -> str:
    """Modifies the state of an agent node in the graph."""
    return update_swarm_node_state_tool(node_id, updates, run_context)

def handoff_create_skill(target_agent_id: str, message: str, run_context: Dict[str, Any]) -> str:
    """Hands off a task or message to another agent node."""
    return create_handoff_edge_tool(target_agent_id, message, run_context)

def trophallaxis_exchange_skill(target_node_id: str, resource: str, amount: float, run_context: Dict[str, Any]) -> str:
    """Executes a resource (energy) transfer to another agent."""
    swarm = run_context["swarm"]
    sender_id = run_context["agent_id"]
    
    sender_node = swarm.graph.nodes.get(sender_id)
    target_node = swarm.graph.nodes.get(target_node_id)
    
    if not sender_node or not target_node:
        return f"Error: Sender ({sender_id}) or Target ({target_node_id}) node not found."
        
    # Get or create edge
    edge_id = f"{sender_id}->{target_node_id}"
    edge = swarm.graph.edges.get(edge_id)
    if not edge or not isinstance(edge, TrophallaxisEdge):
        edge = TrophallaxisEdge(source_id=sender_id, target_id=target_node_id)
        swarm.graph.add_edge(edge)
        
    success = edge.transfer(sender_node, target_node, resource, amount)
    if success:
        return f"Successfully transferred {amount} {resource} from {sender_id} to {target_node_id}"
    else:
        return f"Transfer failed. Check if {sender_id} has sufficient energy above safety limits."

def self_reflect_and_emergence_update_skill(run_context: Dict[str, Any]) -> str:
    """Calculates agent local emergence, adjusts local beliefs and resources."""
    swarm = run_context["swarm"]
    agent_id = run_context["agent_id"]
    agent = swarm.get_agent(agent_id)
    
    if not agent:
        return "Error: Agent not found"
        
    e_contrib = agent.node.compute_local_contribution_to_emergence()
    agent.node.state["last_reflection_time"] = agent.node.state.get("global_time", 0)
    agent.node.state["emergence_contribution"] = e_contrib
    
    # Simple reflection heuristic: reinforce opinions slightly
    main_op = agent.node.opinions.get("main", 0.0)
    agent.node.opinions["main"] = float(main_op * 0.95 + 0.05 * e_contrib)
    
    return f"Reflected. Emergence contribution calculated as: {e_contrib:.3f}. Local memory synchronized."

def spawn_sub_agent_skill(role: str, skills: Optional[List[str]] = None, tools: Optional[List[str]] = None, run_context: Dict[str, Any] = None) -> str:
    """Spawns a child specialist agent linked to the current agent."""
    swarm = run_context["swarm"]
    parent_id = run_context["agent_id"]
    
    # Spawn using role template if found and no specific custom override skills/tools are requested
    if role in swarm.role_templates and not skills and not tools:
        new_agent_id = swarm.spawn_role_agent(role=role, parent_id=parent_id)
    else:
        new_agent_id = swarm.spawn_dynamic_agent(
            role=role,
            initial_skills=skills or [],
            initial_tools=tools or [],
            parent_id=parent_id
        )
    return f"Successfully spawned sub-agent {new_agent_id} with role '{role}'"

def set_control_mode_skill(mode: str, run_context: Dict[str, Any]) -> str:
    """Updates the control mode of the swarm (global or per-node)."""
    swarm = run_context["swarm"]
    try:
        ctrl_mode = ControlMode(mode.upper())
    except ValueError:
        return f"Error: '{mode}' is not a valid ControlMode. Use HIERARCHICAL, DECENTRALIZED, STIGMERGIC, EMERGENCE, or ADAPTIVE."
        
    swarm.set_control_mode(ctrl_mode)
    return f"Swarm control mode successfully set to {ctrl_mode.value}"

def skill_invoke_skill(skill_name: str, arguments: Dict[str, Any], run_context: Dict[str, Any]) -> Any:
    """Meta-skill allowing dynamic/nested execution of other registered skills."""
    registry: SkillRegistry = run_context["skill_registry"]
    target_skill = registry.get_skill(skill_name)
    if not target_skill:
        return f"Error: Skill '{skill_name}' not found."
    return target_skill.execute(**arguments, run_context=run_context)

# --- Setup Helper ---

def setup_core_skills(registry: SkillRegistry):
    """Registers all core skills to the provided SkillRegistry."""
    registry.register_skill(
        name="code_execution",
        description="Executes a Python code block inside a workspace subprocess.",
        when_to_use="When needing to test logic, verify scripts, calculate results, or process data programmatically.",
        input_schema={
            "type": "object",
            "properties": {
                "code": {"type": "string", "description": "The Python code snippet."}
            },
            "required": ["code"]
        },
        func=code_execution_skill,
        risk_level="HIGH"
    )
    
    registry.register_skill(
        name="file_io",
        description="Reads or writes files in the local workspace directory.",
        when_to_use="When reading code files, writing scripts, saving task outputs, or loading local text files.",
        input_schema={
            "type": "object",
            "properties": {
                "operation": {"type": "string", "enum": ["read", "write"], "description": "The operation type."},
                "path": {"type": "string", "description": "Target workspace-relative path."},
                "content": {"type": "string", "description": "Text content to write (only for write operation)."}
            },
            "required": ["operation", "path"]
        },
        func=file_io_skill,
        risk_level="HIGH"
    )
    
    registry.register_skill(
        name="graph_query",
        description="Returns details about the graph nodes (agents) and connection edges.",
        when_to_use="When wanting to inspect the swarm structure, discover neighbor agent roles, check energies, or view communication links.",
        input_schema={
            "type": "object",
            "properties": {}
        },
        func=graph_query_skill,
        risk_level="LOW"
    )
    
    registry.register_skill(
        name="graph_update",
        description="Updates the state metadata or variables of a node.",
        when_to_use="When updating agent beliefs, changing skill configurations, or updating node metrics.",
        input_schema={
            "type": "object",
            "properties": {
                "node_id": {"type": "string", "description": "The ID of the target agent node."},
                "updates": {"type": "object", "description": "The key-value state updates."}
            },
            "required": ["node_id", "updates"]
        },
        func=graph_update_skill,
        risk_level="MEDIUM"
    )
    
    registry.register_skill(
        name="handoff_create",
        description="Sends a task/message to another agent node's inbox.",
        when_to_use="When assigning a task to a specialist, delegating review, or passing results to the coordinator.",
        input_schema={
            "type": "object",
            "properties": {
                "target_agent_id": {"type": "string", "description": "Recipient agent node ID."},
                "message": {"type": "string", "description": "Task context or message description."}
            },
            "required": ["target_agent_id", "message"]
        },
        func=handoff_create_skill,
        risk_level="LOW"
    )
    
    registry.register_skill(
        name="trophallaxis_exchange",
        description="Shares resources (energy) directly with another neighbor agent.",
        when_to_use="When a neighboring node is starving or low on energy, and you want to support swarm equilibrium.",
        input_schema={
            "type": "object",
            "properties": {
                "target_node_id": {"type": "string", "description": "Receiver node ID."},
                "resource": {"type": "string", "default": "energy", "description": "Resource type to share."},
                "amount": {"type": "number", "description": "Resource quantity to transfer."}
            },
            "required": ["target_node_id", "amount"]
        },
        func=trophallaxis_exchange_skill,
        risk_level="LOW"
    )
    
    registry.register_skill(
        name="self_reflect_and_emergence_update",
        description="Computes local emergence contributions and updates node-level parameters.",
        when_to_use="When an agent wants to analyze its progress, update its alignment status, or re-evaluate local opinion states.",
        input_schema={
            "type": "object",
            "properties": {}
        },
        func=self_reflect_and_emergence_update_skill,
        risk_level="LOW"
    )
    
    registry.register_skill(
        name="spawn_sub_agent",
        description="Dynamically spawns a child specialist agent connected to this agent.",
        when_to_use="When a sub-task requires specialized tools or skills that are not active on the current node.",
        input_schema={
            "type": "object",
            "properties": {
                "role": {"type": "string", "description": "The specific role template (e.g. coder, reviewer, system_designer)."},
                "skills": {"type": "array", "items": {"type": "string"}, "description": "Optional list of active skills to inherit."},
                "tools": {"type": "array", "items": {"type": "string"}, "description": "Optional list of active tools to inherit."}
            },
            "required": ["role"]
        },
        func=spawn_sub_agent_skill,
        risk_level="HIGH"
    )
    
    registry.register_skill(
        name="set_control_mode",
        description="Sets the dominant control regime of the swarm (global mode changes).",
        when_to_use="When requiring manual override of agent autonomy or resetting control logic to decentralized/hierarchical.",
        input_schema={
            "type": "object",
            "properties": {
                "mode": {"type": "string", "enum": ["HIERARCHICAL", "DECENTRALIZED", "STIGMERGIC", "EMERGENCE", "ADAPTIVE"]}
            },
            "required": ["mode"]
        },
        func=set_control_mode_skill,
        risk_level="HIGH"
    )
    
    registry.register_skill(
        name="skill_invoke",
        description="Nested meta-skill to invoke another registered skill dynamically.",
        when_to_use="When nesting dynamic skills inside a multi-step sequence.",
        input_schema={
            "type": "object",
            "properties": {
                "skill_name": {"type": "string", "description": "Name of the target skill."},
                "arguments": {"type": "object", "description": "The parameters dict to pass to the target skill."}
            },
            "required": ["skill_name", "arguments"]
        },
        func=skill_invoke_skill,
        risk_level="LOW"
    )
