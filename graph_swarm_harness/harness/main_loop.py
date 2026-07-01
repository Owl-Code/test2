import os
import time
import yaml
from typing import Dict, Any, List, Optional

from base_graph.types import ControlMode, Action, Decision
from base_graph.primitives.node import EmergenceNode
from base_graph.primitives.edge import TrophallaxisEdge

from graph_swarm_harness.core.graph_state import SwarmGraphState, AgentNode
from graph_swarm_harness.core.hybrid_control import HybridControlManager
from graph_swarm_harness.core.emergence import calculate_swarm_emergence

from graph_swarm_harness.tools.registry import ToolRegistry
from graph_swarm_harness.tools.core_tool_implementations import setup_core_tools
from graph_swarm_harness.skills.registry import SkillRegistry
from graph_swarm_harness.skills.core_skill_implementations import setup_core_skills

from graph_swarm_harness.agents.agent_loop import AgentExecutionLoop
from graph_swarm_harness.harness.persistence import save_swarm_state, load_swarm_state, list_checkpoints, checkpoint_to_dict, restore_swarm_from_dict
from graph_swarm_harness.harness.persistence_db import SwarmHistoryDB
from graph_swarm_harness.harness.dashboard import SwarmTerminalDashboard

class SwarmHarnessOrchestrator:
    """Manages the lifecycle, ticks, registries, and observability of the Graph Swarm Harness."""
    
    def __init__(self, config_path: str = "config.yaml"):
        self.config_path = config_path
        self.config = self._load_config()
        
        # Initialize Registries
        self.tool_registry = ToolRegistry()
        setup_core_tools(self.tool_registry)
        
        self.skill_registry = SkillRegistry()
        setup_core_skills(self.skill_registry)
        
        # Load dynamic skills if folder exists
        dynamic_skills_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "skills", "dynamic")
        self.skill_registry.load_skills_from_directory(dynamic_skills_dir)
        
        # Setup Safety and LLM Options
        self.workspace_root = os.path.abspath(self.config.get("workspace_root", "."))
        self.checkpoint_dir = os.path.abspath(self.config.get("checkpoint_dir", "./artifacts/checkpoints"))
        
        self.agent_executor = AgentExecutionLoop(
            model_name=self.config.get("model_name", "qwen2.5:3b-instruct"),
            auto_confirm=self.config.get("auto_confirm_high_risk", False)
        )
        
        self.control_manager = HybridControlManager(
            target_cohesion=self.config.get("mode_switching", {}).get("target_cohesion", 0.85),
            emergency_energy_threshold=self.config.get("mode_switching", {}).get("emergency_energy_threshold", 35.0)
        )
        
        self.dashboard = SwarmTerminalDashboard()
        
        # Initialize SQLite history database
        db_path = os.path.join(self.checkpoint_dir, "swarm_history.db")
        self.history_db = SwarmHistoryDB(db_path=db_path)
        self.swarm: Optional[SwarmGraphState] = None
        self.active_agents_this_tick: List[str] = []

    def _load_config(self) -> Dict[str, Any]:
        if os.path.exists(self.config_path):
            with open(self.config_path, "r") as f:
                return yaml.safe_load(f) or {}
        return {
            "model_name": "qwen2.5:3b-instruct",
            "workspace_root": ".",
            "checkpoint_dir": "./artifacts/checkpoints",
            "auto_confirm_high_risk": False,
            "max_active_agents_per_tick": 2,
            "mode_switching": {
                "target_cohesion": 0.85,
                "emergency_energy_threshold": 35.0
            }
        }

    def setup_swarm(self, resume: bool = True) -> SwarmGraphState:
        """Loads the latest checkpoint if available and requested, otherwise bootstrap a default coordinator swarm."""
        checkpoints = list_checkpoints(self.checkpoint_dir)
        
        if resume and checkpoints:
            latest = checkpoints[0]
            print(f"Resuming swarm from checkpoint: {latest}")
            self.swarm = load_swarm_state(latest)
        else:
            print("Bootstrapping a new graph swarm...")
            self.swarm = SwarmGraphState(name="swarm-alpha")
            self.swarm.active_goals = ["Coordinate and assign system design analysis."]
            self.swarm.goal_energy = {
                "Coordinate and assign system design analysis.": 100.0
            }
            
            # Spawn default role agents
            coord_id = self.swarm.spawn_role_agent(role="coordinator")
            self.swarm.spawn_role_agent(role="coder", parent_id=coord_id)
            self.swarm.spawn_role_agent(role="reviewer", parent_id=coord_id)
            
        # Register policies on all nodes
        self._bind_swarm_policies()
        return self.swarm

    def _bind_swarm_policies(self):
        """Binds policy callbacks to each node to intercept hybrid_step decisions."""
        for node in self.swarm.graph.nodes.values():
            if isinstance(node, EmergenceNode):
                node.policy = self._swarm_node_policy_callback

    def _swarm_node_policy_callback(self, node: EmergenceNode, action_space: List[Action], context: Dict[str, Any]) -> Decision:
        """Callback intercepted during hybrid_step. Routes to LLM or fallback heuristics."""
        agent_id = str(node.id)
        
        # Sparse activation check: is this node active for LLM step this tick?
        if agent_id not in self.active_agents_this_tick:
            # Low energy check: if starving, fallback immediately to rule-based homeostasis search
            if node.resources.get("energy", 100.0) < 20.0:
                for act in action_space:
                    if act.action_type == "SEARCH_RESOURCE":
                        # Simulate simple local resource foraging to boost energy
                        node.resources["energy"] = min(100.0, node.resources["energy"] + 15.0)
                        return Decision(
                            node_id=agent_id,
                            selected_action=act,
                            confidence=0.99,
                            reason="Starving rule-based homeostatic override: found energy resources."
                        )
            
            # Base DeGroot consensus opinion convergence fallback
            if node.control_mode == ControlMode.DECENTRALIZED:
                neighbors = context.get("neighbors", [])
                if neighbors:
                    my_op = node.opinions.get("main", 0.0)
                    avg_op = sum(n.opinions.get("main", 0.0) for n in neighbors if hasattr(n, "opinions")) / len(neighbors)
                    node.opinions["main"] = my_op + 0.1 * (avg_op - my_op)
                    
                    for act in action_space:
                        if act.action_type == "CONVERGE_OPINION":
                            return Decision(
                                node_id=agent_id,
                                selected_action=act,
                                confidence=0.8,
                                reason="Fallback DeGroot opinion convergence step."
                            )
                            
            # Default idle behavior to save local model execution tokens
            return Decision(
                node_id=agent_id,
                selected_action=Action(action_type="idle", parameters={}),
                confidence=0.5,
                reason="Agent inactive this tick; rule-based conserving state."
            )

        # Check precomputed decisions from parallel tick
        if hasattr(self, "precomputed_decisions") and agent_id in self.precomputed_decisions:
            return self.precomputed_decisions[agent_id]
            
        # Default idle behavior to save local model execution tokens
        return Decision(
            node_id=agent_id,
            selected_action=Action(action_type="idle", parameters={}),
            confidence=0.5,
            reason="Agent inactive this tick; rule-based conserving state."
        )

    def select_active_agents(self) -> List[str]:
        """Runs the expert sparse routing to select which nodes get LLM attention this tick."""
        agents = self.swarm.get_agents()
        if not agents:
            return []
            
        active_ids = []
        
        # 1. Always prioritize the Coordinator if active
        coordinators = [a for a in agents if a.role == "coordinator"]
        for coord in coordinators:
            active_ids.append(coord.id)
            
        # 2. Prioritize agents with unread messages in their inbox
        for agent in agents:
            if agent.id not in active_ids:
                unread = [m for m in agent.inbox if not m.get("read", False)]
                if unread:
                    active_ids.append(agent.id)
                    
        # 3. Fill up to limit with agents having lowest energy or highest emergence variance
        limit = self.config.get("max_active_agents_per_tick", 2)
        if len(active_ids) < limit:
            remaining_agents = [a for a in agents if a.id not in active_ids]
            # Sort by lowest energy
            remaining_agents.sort(key=lambda a: a.energy)
            for ra in remaining_agents:
                if len(active_ids) >= limit:
                    break
                active_ids.append(ra.id)
                
        self.active_agents_this_tick = active_ids[:limit]
        return self.active_agents_this_tick

    async def run_tick(self) -> str:
        """Executes one single simulation tick, including routing, hybrid step, and persistence."""
        if not self.swarm:
            raise ValueError("Swarm not initialized. Call setup_swarm first.")
            
        # Select active nodes for this step
        self.select_active_agents()
        
        # Record pre-step agent state logs for dashboard
        log_parts = []
        for aid in self.active_agents_this_tick:
            agent = self.swarm.get_agent(aid)
            if agent:
                log_parts.append(f"- Active Agent [bold yellow]{aid}[/bold yellow] ({agent.role}) routed for execution.")
                
        # Bind policies dynamically (covers newly spawned nodes)
        self._bind_swarm_policies()
        
        # Step active agents concurrently using async/await
        import asyncio
        tasks = []
        for aid in self.active_agents_this_tick:
            tasks.append(self.agent_executor.step_agent(
                swarm=self.swarm,
                agent_id=aid,
                tool_registry=self.tool_registry,
                skill_registry=self.skill_registry,
                workspace_root=self.workspace_root
            ))
            
        if tasks:
            decisions = await asyncio.gather(*tasks)
            self.precomputed_decisions = {aid: dec for aid, dec in zip(self.active_agents_this_tick, decisions)}
        else:
            self.precomputed_decisions = {}
            
        # Reset local memories of inactive nodes to prevent lingering/stale thoughts in UI
        all_agent_ids = [a.id for a in self.swarm.get_agents()]
        for aid in all_agent_ids:
            if aid not in self.active_agents_this_tick:
                agent = self.swarm.get_agent(aid)
                if agent:
                    agent.node.local_memory["last_thought"] = "Resting/Conserving state"
                    agent.node.local_memory["last_decision_reason"] = "Agent inactive this tick; rule-based conserving state."
                    
        # Execute hybrid step (routes policy calls internally)
        step_res = self.swarm.hybrid_step()
        
        # Mark inbox messages as read for active agents
        for aid in self.active_agents_this_tick:
            agent = self.swarm.get_agent(aid)
            if agent:
                for msg in agent.inbox:
                    msg["read"] = True
                    
        # Stigmergic/DeGroot diffusion spreading
        self.swarm.diffusion_subgraph.run_diffusion(model="opinion", steps=2)
        
        # Evaluate health and adaptively switch mode if global mode is ADAPTIVE
        global_mode = self.swarm.get_agents()[0].node.control_mode if self.swarm.get_agents() else ControlMode.EMERGENCE
        if global_mode == ControlMode.EMERGENCE:
            # We can run adaptive checks
            new_mode = self.control_manager.evaluate_and_adapt(self.swarm, step_res.health)
            if new_mode != global_mode.value:
                log_parts.append(f"[MODE] System Mode adapted from [bold]{global_mode.value}[/bold] to [bold]{new_mode}[/bold].")

        # Save checkpoint
        save_path = save_swarm_state(self.swarm, self.checkpoint_dir)
        log_parts.append(f"[SAVE] Checkpoint saved: [dim]{os.path.basename(save_path)}[/dim]")
        
        # Save to SQLite DB history logs
        try:
            state_dict = checkpoint_to_dict(self.swarm)
            emergence = calculate_swarm_emergence(self.swarm)
            db_hash = self.history_db.save_checkpoint(self.swarm.step_index, state_dict, emergence)
            log_parts.append(f"[DB] SQLite checkpoint saved (Hash: {db_hash[:8]}...)")
        except Exception as e:
            log_parts.append(f"[DB ERROR] SQLite save failed: {e}")
            
        # Render dashboard
        log_summary = "\n".join(log_parts)
        self.dashboard.render(self.swarm, log_summary)
        
        return log_summary
        
    async def loop(self, ticks: int = 10, delay: float = 1.0):
        """Runs the harness loop for a specified number of ticks."""
        import asyncio
        for _ in range(ticks):
            await self.run_tick()
            await asyncio.sleep(delay)

    def rollback_to_tick(self, tick: int) -> str:
        """Rolls back the active swarm graph state to a historical DB checkpoint."""
        state_dict = self.history_db.load_checkpoint(tick)
        if not state_dict:
            raise ValueError(f"No checkpoint found in SQLite for tick #{tick}")
            
        self.swarm = restore_swarm_from_dict(state_dict)
        return f"Successfully rolled back active swarm state to tick #{tick}"
