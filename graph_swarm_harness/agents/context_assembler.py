from typing import Dict, Any, List
from graph_swarm_harness.core.graph_state import SwarmGraphState, AgentNode
from graph_swarm_harness.tools.registry import ToolRegistry
from graph_swarm_harness.skills.registry import SkillRegistry

def assemble_agent_context(
    swarm: SwarmGraphState, 
    agent: AgentNode, 
    tool_registry: ToolRegistry, 
    skill_registry: SkillRegistry,
    diffusion_steps: int = 3
) -> Dict[str, Any]:
    """Assembles all local, neighbor, global, and capability details for an agent's step."""
    
    # 1. Local state details
    local_state = {
        "id": agent.id,
        "role": agent.role,
        "energy": agent.energy,
        "opinions": agent.node.opinions.copy(),
        "beliefs": agent.beliefs.copy(),
        "short_term_memory": list(agent.short_term_memory),
        "control_mode": agent.node.control_mode.value,
        "emergence_contribution": agent.emergence_level
    }
    
    # 2. Neighbors info
    neighbors_list = []
    # get raw outgoing neighbor nodes from base graph
    raw_neighbors = swarm.graph.get_neighbors(agent.id)
    for n in raw_neighbors:
        n_agent = swarm.get_agent(str(n.id))
        if n_agent:
            neighbors_list.append({
                "id": n_agent.id,
                "role": n_agent.role,
                "energy": n_agent.energy,
                "opinions": n_agent.node.opinions.copy(),
                "emergence_contribution": n_agent.emergence_level
            })
            
    # 3. Inbox messages
    inbox_messages = [msg for msg in agent.inbox if not msg.get("read", False)]
    
    # 4. Global parameters
    global_state = {
        "active_goals": list(swarm.active_goals),
        "step_index": swarm.step_index,
        "total_agents": len(swarm.get_agents()),
        "name": swarm.name
    }
    
    # 5. Filter tools and skills matching the agent's permissions
    tool_catalog = []
    for tname in agent.available_tools:
        tool = tool_registry.get_tool(tname)
        if tool:
            tool_catalog.append({
                "name": tool.name,
                "description": tool.description,
                "parameters": tool.parameters
            })
            
    skill_catalog = []
    for sname in agent.active_skills:
        skill = skill_registry.get_skill(sname)
        if skill:
            skill_catalog.append({
                "name": skill.name,
                "description": skill.description,
                "when_to_use": skill.when_to_use,
                "input_schema": skill.input_schema
            })
            
    # Check for diffused signal potentials in the node's local memory
    diffused_signals = agent.node.local_memory.get("stigmergy_deposits", [])
    
    return {
        "local": local_state,
        "neighbors": neighbors_list,
        "inbox": inbox_messages,
        "global": global_state,
        "available_tools": tool_catalog,
        "available_skills": skill_catalog,
        "diffused_signals": diffused_signals
    }
