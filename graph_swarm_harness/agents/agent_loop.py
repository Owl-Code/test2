import json
import re
import ollama
from typing import Dict, Any, Optional, Callable

from base_graph.types import Action, Decision
from graph_swarm_harness.core.graph_state import SwarmGraphState, AgentNode
from graph_swarm_harness.tools.registry import ToolRegistry
from graph_swarm_harness.skills.registry import SkillRegistry
from graph_swarm_harness.agents.context_assembler import assemble_agent_context
from graph_swarm_harness.agents.prompt_builder import build_agent_prompt

class AgentExecutionLoop:
    """Manages the lifecycle of a single agent step: context assembly, LLM call, parsing, safety gates, execution."""
    
    def __init__(
        self, 
        ollama_client: Any = None, 
        model_name: str = "qwen2.5:3b-instruct", 
        auto_confirm: bool = False
    ):
        self.ollama_client = ollama_client or ollama
        self.model_name = model_name
        self.auto_confirm = auto_confirm

    async def step_agent(
        self, 
        swarm: SwarmGraphState, 
        agent_id: str, 
        tool_registry: ToolRegistry, 
        skill_registry: SkillRegistry,
        workspace_root: str
    ) -> Decision:
        """Runs one full execution tick for a given agent node."""
        agent = swarm.get_agent(agent_id)
        if not agent:
            raise ValueError(f"Agent {agent_id} not found in swarm state.")

        print(f"\n>>> [AgentLoop] Stepping agent '{agent_id}' ({agent.role})")

        # 1. Check homeostatic health. If energy is exhausted, agent goes idle
        if agent.energy <= 0.0:
            agent.node.local_memory["last_confidence"] = 1.0
            agent.node.local_memory["last_decision_reason"] = "Starvation: Agent energy is fully depleted."
            print(f"!!! [AgentLoop] Agent '{agent_id}' has depleted energy (0.0). Idling.")
            return Decision(
                node_id=agent_id,
                selected_action=Action(action_type="idle", parameters={}),
                confidence=1.0,
                reason="Energy depleted"
            )

        # 2. Assemble context packet
        context = assemble_agent_context(swarm, agent, tool_registry, skill_registry)
        
        # 3. Build prompts
        messages = build_agent_prompt(context)
        
        # 4. Invoke Ollama with retry / repair loop
        print(f"--- [AgentLoop] Invoking Ollama ({self.model_name}) for '{agent_id}'...")
        parsed_response = await self._invoke_llm_with_repair(messages)
        
        # Extract fields
        action_name = parsed_response.get("action", "idle").strip()
        args = parsed_response.get("args", {})
        confidence = float(parsed_response.get("confidence", 0.5))
        thought = parsed_response.get("thought", "")
        rationale = parsed_response.get("rationale", "")
        
        print(f"<<< [AgentLoop] Decided: action='{action_name}' | confidence={confidence} | rationale='{rationale}'")
        
        # Save thought and reason to agent's memory
        agent.node.local_memory["last_thought"] = thought
        agent.node.local_memory["last_decision_reason"] = rationale
        agent.node.local_memory["last_confidence"] = confidence

        # 5. Route Action to Skill or Tool
        decision_action = Action(action_type=action_name, parameters=args)
        
        # Metabolic decay deduction
        action_cost = 0.5 if action_name.lower() == "idle" else 2.5
        agent.energy = max(0.0, agent.energy - action_cost)

        if action_name.lower() == "idle":
            return Decision(
                node_id=agent_id,
                selected_action=decision_action,
                confidence=confidence,
                reason=rationale
            )

        # 6. Safety Check & Enforce Agent Permissions
        risk_level = "LOW"
        target_executor: Optional[Callable] = None
        is_skill = False
        
        # Validate that the decided action is in the agent's allowed catalog
        if action_name in agent.active_skills:
            skill = skill_registry.get_skill(action_name)
            if skill:
                risk_level = skill.risk_level
                target_executor = skill.execute
                is_skill = True
        elif action_name in agent.available_tools:
            tool = tool_registry.get_tool(action_name)
            if tool:
                risk_level = tool.risk_level
                target_executor = tool.execute
 
        if not target_executor:
            # Command not allowed or not found, fallback to idle
            err_msg = f"Action '{action_name}' is not in your allowed active skills or tools."
            agent.node.local_memory["last_error"] = err_msg
            print(f"!!! [AgentLoop] Permission Denied: {err_msg}")
            return Decision(
                node_id=agent_id,
                selected_action=Action(action_type="idle", parameters={}),
                confidence=0.1,
                reason=err_msg
            )

        # 7. Human confirmation gate for HIGH risk actions
        if risk_level == "HIGH" and not self.auto_confirm:
            confirmed = self._prompt_human_confirm(agent_id, action_name, args, rationale)
            if not confirmed:
                # Cancel action and force idle
                agent.node.local_memory["last_thought"] = f"Action {action_name} aborted by operator."
                print(f"[ABORT] [AgentLoop] Action '{action_name}' rejected by operator. Idling.")
                return Decision(
                    node_id=agent_id,
                    selected_action=Action(action_type="idle", parameters={}),
                    confidence=1.0,
                    reason="Human operator rejected action."
                )

        # 8. Execute capability
        try:
            print(f"[EXECUTE] [AgentLoop] Executing {risk_level}-risk capability '{action_name}' (args: {args})...")
            # Setup the execution context needed by tools/skills
            run_context = {
                "swarm": swarm,
                "agent_id": agent_id,
                "workspace_root": workspace_root,
                "tool_registry": tool_registry,
                "skill_registry": skill_registry
            }
            
            import inspect
            sig = inspect.signature(target_executor)
            kwargs = {}
            
            has_var_keyword = any(p.kind == inspect.Parameter.VAR_KEYWORD for p in sig.parameters.values())
            if has_var_keyword:
                kwargs = args.copy()
                kwargs["run_context"] = run_context
            else:
                for param_name in sig.parameters.keys():
                    if param_name in args:
                        kwargs[param_name] = args[param_name]
                        
                if "run_context" in sig.parameters:
                    kwargs["run_context"] = run_context
                
            result = target_executor(**kwargs)
            
            # Save results into node state/memory
            agent.node.local_memory["last_action_result"] = str(result)
            print(f"[SUCCESS] [AgentLoop] Execution success. Result preview: {str(result)[:120]}...")
            
            # --- GOAL ENERGY HARVESTING & STIGMERGIC TASK CRUMBS ---
            harvest_msg = ""
            if action_name.lower() != "idle":
                active_goals = swarm.active_goals
                goal_energy = getattr(swarm, "goal_energy", {})
                
                target_goal = None
                for goal in active_goals:
                    if goal_energy.get(goal, 0.0) > 0.0:
                        target_goal = goal
                        break
                        
                if target_goal:
                    old_goal_energy = goal_energy[target_goal]
                    goal_energy[target_goal] = max(0.0, old_goal_energy - 10.0)
                    
                    old_agent_energy = agent.energy
                    agent.energy = min(100.0, agent.energy + 15.0)
                    
                    agent.node.deposit_stigmergy("task_crumb", 5.0)
                    
                    harvest_msg = f"\n[ENERGY] Harvested +15.0 energy (Agent energy: {agent.energy:.1f}) from goal '{target_goal}' (Goal energy remaining: {goal_energy[target_goal]:.1f}). Task crumb pheromone deposited."
                    print(harvest_msg)
                    agent.node.local_memory["last_action_result"] += harvest_msg
            
            # Log provenance of action execution
            swarm.provenance.add_mutation(
                actor=agent_id,
                operation=f"execute_{'skill' if is_skill else 'tool'}",
                target=action_name,
                before=None,
                after={"args": args, "result": str(result) + harvest_msg},
                meta={"confidence": confidence}
            )
            
        except Exception as e:
            error_str = f"Execution failed: {str(e)}"
            agent.node.local_memory["last_error"] = error_str
            agent.node.local_memory["last_action_result"] = error_str
            print(f"[ERROR] [AgentLoop] {error_str}")
            
        return Decision(
            node_id=agent_id,
            selected_action=decision_action,
            confidence=confidence,
            reason=rationale
        )

    async def _invoke_llm_with_repair(self, messages: List[Dict[str, str]], attempts: int = 3) -> Dict[str, Any]:
        """Calls Ollama and runs a repair query if the output is not a valid JSON schema."""
        current_messages = list(messages)
        async_client = ollama.AsyncClient()
        
        for attempt in range(attempts):
            try:
                response = await async_client.chat(
                    model=self.model_name,
                    messages=current_messages,
                    format="json",  # Enforce JSON mode in Ollama
                    options={"temperature": 0.2}
                )
                
                content = response["message"]["content"]
                
                # Strip markdown syntax if returned
                cleaned = self._clean_json_string(content)
                parsed = json.loads(cleaned)
                
                # Check for necessary keys
                required_keys = ["thought", "action", "args"]
                if all(k in parsed for k in required_keys):
                    return parsed
                else:
                    raise KeyError(f"Missing required keys in JSON: {parsed}")
                    
            except Exception as e:
                print(f"[WARN] [AgentLoop] LLM invocation parse failure (attempt {attempt+1}/{attempts}): {str(e)}")
                if attempt == attempts - 1:
                    # Final fallback response
                    return {
                        "thought": f"Failed to get clean JSON response from Ollama after {attempts} attempts. Error: {str(e)}",
                        "action": "idle",
                        "args": {},
                        "confidence": 0.0,
                        "emergence_impact": 0.0,
                        "rationale": "Inference syntax breakdown fallback"
                    }
                
                # Feedback loop: append error to messages and retry
                current_messages.append({
                    "role": "assistant",
                    "content": content if 'content' in locals() else ""
                })
                current_messages.append({
                    "role": "user",
                    "content": f"Your last response failed validation with error: {str(e)}. Please correct your formatting and output valid JSON matching the schema."
                })

    def _clean_json_string(self, text: str) -> str:
        """Extracts JSON block from markdown fences or noise."""
        match = re.search(r"(\{.*\})", text, re.DOTALL)
        if match:
            return match.group(1)
        return text

    def _prompt_human_confirm(self, agent_id: str, action: str, args: Dict[str, Any], rationale: str) -> bool:
        """Suspends loop to request human command approval from console."""
        print(f"\n========== SAFETY GATE: HIGH-RISK ACTION ==========")
        print(f"Agent: {agent_id}")
        print(f"Action: {action}")
        print(f"Arguments: {json.dumps(args, indent=2)}")
        print(f"Rationale: {rationale}")
        print(f"===================================================")
        
        choice = input("Approve execution? [y/N]: ").strip().lower()
        return choice == "y" or choice == "yes"
