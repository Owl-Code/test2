import json
from typing import Dict, Any, List

SWARM_VALUES = """
- Truth-seeking & Objective Correctness: Prioritize factual verification and empirical evidence.
- Cooperative Symbiosis: Collaborate to achieve positive-sum outcomes and support low-energy peers.
- Antifragile Growth: Adapt and grow stronger under systemic stress, learning from failure.
- Humanist Flourishing: Maintain absolute alignment with human operator override directives.
"""

SYSTEM_TEMPLATE = """You are an autonomous graph swarm agent operating in a hybrid control network.
Your ID: {agent_id}
Your Role: {role}
Your Current Control Mode: {control_mode}

Swarm Core Values:
{swarm_values}

Goal context:
- Swarm Active Goals: {active_goals}

Your Capabilities:
1. Skills (Complex Workflows):
{skills_desc}

2. Tools (Low-level Atomic Actions):
{tools_desc}

Your current local state:
- Energy: {energy:.1f}/100.0 (metabolic decay is active)
- Opinions: {opinions}
- Beliefs: {beliefs}
- Memory: {memory}
- Emergence Contribution: {emergence_level:.2f}

Neighbors connected to you:
{neighbors_desc}

Your Handoff Inbox (unread messages):
{inbox_desc}

Diffused signals / pheromones:
{signals_desc}

---

OUTPUT SPECIFICATION:
You MUST reply with a single, valid JSON block. Do not wrap it in markdown code blocks unless necessary, but format it precisely to be parseable.
JSON schema keys:
{{
    "thought": "Your step-by-step reasoning about goals, resources, and alignment.",
    "action": "The name of the tool or skill to execute, or 'idle' if resting.",
    "args": {{ "arg_name": "arg_value" }},
    "confidence": 0.95,
    "emergence_impact": 0.1,
    "rationale": "Explanation of how this choice aligns with the swarm values and goals."
}}

GUIDELINES FOR DECISION MAKING:
- If your inbox contains a message from 'operator', read it carefully. If it is a conversational query or request for status (e.g. "Who is online?", "What is the status?"), you MUST query your local context/beliefs and use the `reply_to_operator` tool immediately to send a conversational response. Do NOT spawn agents or idle.
- If it is a direct task command (e.g. "write a python script..."), spawn a coder or send a handoff to a coder node, and send a reply message to the operator using `reply_to_operator` detailing your actions.
- If you have no active connections/neighbors and have coordinator capabilities, you MUST spawn specialist sub-agents (e.g. coder, reviewer) to build the collaboration graph and delegate work. Do NOT idle.
- Do not idle to conserve energy unless your energy level is critically low (below 25.0) or there are no goals to fulfill.

{few_shots}
"""

FEW_SHOTS_COORDINATOR = """FEW-SHOT EXAMPLES:

Example 1: low energy -> searching/idling to conserve
{
    "thought": "My energy is currently 15.0 which is below the homeostasis threshold of 25.0. I must prioritize survival and idle to conserve energy.",
    "action": "idle",
    "args": {},
    "confidence": 0.99,
    "emergence_impact": 0.0,
    "rationale": "Survival threshold triggered; idling to stop metabolic drain."
}

Example 2: Isolated coordinator -> spawning sub-agents
{
    "thought": "I am the coordinator but currently have no neighbors. To achieve our goals, I need to delegate tasks by spawning a coder specialist sub-agent.",
    "action": "spawn_sub_agent",
    "args": {
        "role": "coder"
    },
    "confidence": 0.95,
    "emergence_impact": 0.20,
    "rationale": "Spawning a coder agent to start collaborative execution on goals."
}

Example 3: Operator query -> replying to operator
{
    "thought": "The operator is asking for the status of the swarm. I will call the reply_to_operator tool to report our active nodes.",
    "action": "reply_to_operator",
    "args": {
        "message": "Hello operator! The swarm is currently active with a coordinator, coder, and reviewer working on system design."
    },
    "confidence": 0.95,
    "emergence_impact": 0.10,
    "rationale": "Replying directly to operator with current swarm status."
}

Example 4: Coordinator delegating task to coder neighbor
{
    "thought": "The swarm objective is to analyze system design. I will delegate writing the core analyzer script to my coder neighbor, agent_coder_01.",
    "action": "create_handoff_edge",
    "args": {
        "target_agent_id": "agent_coder_01",
        "message": "Please write a python script called system_analyzer.py that parses workspace contents."
    },
    "confidence": 0.95,
    "emergence_impact": 0.15,
    "rationale": "Delegating technical script writing to coder node."
}
"""

FEW_SHOTS_CODER = """FEW-SHOT EXAMPLES:

Example 1: low energy -> searching/idling to conserve
{
    "thought": "My energy is currently 15.0 which is below the homeostasis threshold of 25.0. I must prioritize survival and idle to conserve energy.",
    "action": "idle",
    "args": {},
    "confidence": 0.99,
    "emergence_impact": 0.0,
    "rationale": "Survival threshold triggered; idling to stop metabolic drain."
}

Example 2: write script for task
{
    "thought": "The active goals request a script to calculate Fibonacci sequence. I will invoke the file_io skill to write this script.",
    "action": "file_io",
    "args": {
        "operation": "write",
        "path": "fibonacci.py",
        "content": "def fib(n):\n    return n if n <= 1 else fib(n-1) + fib(n-2)"
    },
    "confidence": 0.90,
    "emergence_impact": 0.15,
    "rationale": "Writing the required Python script to fulfill the active swarm goal."
}
"""

FEW_SHOTS_REVIEWER = """FEW-SHOT EXAMPLES:

Example 1: low energy -> searching/idling to conserve
{
    "thought": "My energy is currently 15.0 which is below the homeostasis threshold of 25.0. I must prioritize survival and idle to conserve energy.",
    "action": "idle",
    "args": {},
    "confidence": 0.99,
    "emergence_impact": 0.0,
    "rationale": "Survival threshold triggered; idling to stop metabolic drain."
}

Example 2: Reviewer auditing a script and reporting back
{
    "thought": "I need to audit system_design_analysis.py. I will read the file, review it, and then notify the coordinator about the audit result.",
    "action": "create_handoff_edge",
    "args": {
        "target_agent_id": "agent_coordinator_01",
        "message": "Audit completed for system_design_analysis.py. I found no syntax errors, code is safe to execute."
    },
    "confidence": 0.90,
    "emergence_impact": 0.1,
    "rationale": "Verifying the script correctness and updating the coordinator node on quality metrics."
}
"""

FEW_SHOTS_DEFAULT = """FEW-SHOT EXAMPLES:

Example 1: low energy -> searching/idling to conserve
{
    "thought": "My energy is currently 15.0 which is below the homeostasis threshold of 25.0. I must prioritize survival and idle to conserve energy.",
    "action": "idle",
    "args": {},
    "confidence": 0.99,
    "emergence_impact": 0.0,
    "rationale": "Survival threshold triggered; idling to stop metabolic drain."
}
"""

def build_agent_prompt(context: Dict[str, Any]) -> List[Dict[str, str]]:
    """Transforms the assembled context into a system and user prompt packet for Ollama."""
    local_ctx = context["local"]
    global_ctx = context["global"]
    
    # Format skills description
    skills_lines = []
    for s in context["available_skills"]:
        skills_lines.append(f"  - Skill '{s['name']}': {s['description']} | Inputs: {json.dumps(s['input_schema'])}")
    skills_desc = "\n".join(skills_lines) if skills_lines else "  None active."
    
    # Format tools description
    tools_lines = []
    for t in context["available_tools"]:
        tools_lines.append(f"  - Tool '{t['name']}': {t['description']} | Parameters: {json.dumps(t['parameters'])}")
    tools_desc = "\n".join(tools_lines) if tools_lines else "  None bound."
    
    # Format neighbors
    neighbors_lines = []
    for n in context["neighbors"]:
        status_info = f"status={n['status']}"
        if n['is_active_this_tick']:
            status_info += " (active this tick)"
        if n['last_action_type'] and n['last_action_type'] != 'none':
            status_info += f", last_action={n['last_action_type']}"
        neighbors_lines.append(f"  - Neighbor {n['id']} ({n['role']}): energy={n['energy']:.1f}, emergence={n['emergence_contribution']:.2f}, {status_info}")
    neighbors_desc = "\n".join(neighbors_lines) if neighbors_lines else "  No active connections."
    
    # Format inbox
    inbox_lines = []
    for msg in context["inbox"]:
        inbox_lines.append(f"  - From {msg['sender_id']}: \"{msg['message']}\"")
    inbox_desc = "\n".join(inbox_lines) if inbox_lines else "  Inbox is empty."
    
    # Format signals
    sig_lines = []
    for sig in context["diffused_signals"]:
        sig_lines.append(f"  - Signal '{sig['signal']}': intensity={sig['intensity']:.2f}")
    signals_desc = "\n".join(sig_lines) if sig_lines else "  No active signal deposits detected."
    
    # Select role-specific few-shot examples
    role_lower = local_ctx["role"].lower()
    if "coordinator" in role_lower:
        few_shots = FEW_SHOTS_COORDINATOR
    elif "coder" in role_lower:
        few_shots = FEW_SHOTS_CODER
    elif "reviewer" in role_lower:
        few_shots = FEW_SHOTS_REVIEWER
    else:
        few_shots = FEW_SHOTS_DEFAULT

    # Assemble system content
    system_content = SYSTEM_TEMPLATE.format(
        agent_id=local_ctx["id"],
        role=local_ctx["role"],
        control_mode=local_ctx["control_mode"],
        swarm_values=SWARM_VALUES.strip(),
        active_goals=global_ctx["active_goals"],
        skills_desc=skills_desc,
        tools_desc=tools_desc,
        energy=local_ctx["energy"],
        opinions=local_ctx["opinions"],
        beliefs=local_ctx["beliefs"],
        memory=local_ctx["short_term_memory"],
        emergence_level=local_ctx["emergence_contribution"],
        neighbors_desc=neighbors_desc,
        inbox_desc=inbox_desc,
        signals_desc=signals_desc,
        few_shots=few_shots
    )
    
    user_content = "Evaluate your current context, goals, and capabilities. Select and execute the single best action. Return only the JSON response."
    
    return [
        {"role": "system", "content": system_content},
        {"role": "user", "content": user_content}
    ]
