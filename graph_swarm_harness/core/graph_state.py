import uuid
import os
import yaml
from typing import Any, Dict, List, Optional, Union

from base_graph.core.hybrid_swarm import HybridControlSwarmGraph
from base_graph.primitives.node import EmergenceNode
from base_graph.primitives.edge import TrophallaxisEdge, EmergenceEdge, AdaptiveEdge
from base_graph.types import ControlMode, EdgeType

class AgentNode:
    """Helper interface wrapping an EmergenceNode to manage agent-specific state attributes.
    
    Stores everything inside the node's `state` dict to preserve base_graph serialization and hashing.
    """
    def __init__(self, node: EmergenceNode):
        self.node = node

    @property
    def id(self) -> str:
        return str(self.node.id)

    @property
    def role(self) -> str:
        return self.node.state.get("role", "generalist")

    @role.setter
    def role(self, value: str):
        self.node.state["role"] = value

    @property
    def active_skills(self) -> List[str]:
        return self.node.state.setdefault("active_skills", [])

    @active_skills.setter
    def active_skills(self, value: List[str]):
        self.node.state["active_skills"] = value

    @property
    def available_tools(self) -> List[str]:
        return self.node.state.setdefault("available_tools", [])

    @available_tools.setter
    def available_tools(self, value: List[str]):
        self.node.state["available_tools"] = value

    @property
    def inbox(self) -> List[Dict[str, Any]]:
        return self.node.state.setdefault("inbox", [])

    def receive_message(self, sender_id: str, message: str, meta: Optional[Dict[str, Any]] = None):
        """Appends an incoming handoff/communication message to the inbox."""
        self.inbox.append({
            "sender_id": sender_id,
            "message": message,
            "meta": meta or {},
            "read": False
        })

    def clear_inbox(self):
        self.node.state["inbox"] = []

    @property
    def beliefs(self) -> Dict[str, Any]:
        return self.node.state.setdefault("beliefs", {})

    @property
    def short_term_memory(self) -> List[str]:
        return self.node.state.setdefault("short_term_memory", [])

    @property
    def last_action(self) -> Optional[Dict[str, Any]]:
        return self.node.local_memory.get("last_action")

    @property
    def emergence_level(self) -> float:
        return self.node.compute_local_contribution_to_emergence()

    @property
    def energy(self) -> float:
        return self.node.resources.get("energy", 100.0)

    @energy.setter
    def energy(self, value: float):
        self.node.resources["energy"] = value

class SwarmGraphState(HybridControlSwarmGraph):
    """Extends HybridControlSwarmGraph to support dynamic agent spawning and harness loops."""
    
    def __init__(self, name: str = "swarm-harness-001", seed: Optional[int] = None) -> None:
        super().__init__(name=name, seed=seed)
        self.active_goals: List[str] = []
        self.chat_replies: List[Dict[str, Any]] = []
        self.intra_swarm_messages: List[Dict[str, Any]] = []
        self.role_templates: Dict[str, Any] = {}
        self._load_default_roles()

    def _load_default_roles(self) -> None:
        curr_dir = os.path.dirname(os.path.abspath(__file__))
        roles_path = os.path.join(curr_dir, "roles.yaml")
        if os.path.exists(roles_path):
            try:
                with open(roles_path, "r", encoding="utf-8") as f:
                    self.role_templates = yaml.safe_load(f) or {}
            except Exception as e:
                print(f"[SwarmGraphState] Warning: Failed to load roles.yaml: {e}")

    def spawn_role_agent(self, role: str, parent_id: Optional[str] = None) -> str:
        """Spawns an agent node using parameters defined in the role template registry."""
        config = self.role_templates.get(role, {"skills": [], "tools": [], "persona": ""})
        agent_id = self.spawn_dynamic_agent(
            role=role,
            initial_skills=config.get("skills", []),
            initial_tools=config.get("tools", []),
            parent_id=parent_id
        )
        agent = self.get_agent(agent_id)
        if agent:
            agent.beliefs["persona"] = config.get("persona", "")
        return agent_id

    def update_role_template(self, role: str, config: Dict[str, Any]):
        """Modifies or adds a role configuration template at runtime, logging to provenance."""
        before = self.role_templates.get(role)
        self.role_templates[role] = config
        
        self.provenance.add_mutation(
            actor="operator",
            operation="update_role_template",
            target=role,
            before=before,
            after=config
        )

    def get_agent(self, node_id: str) -> Optional[AgentNode]:
        node = self.graph.nodes.get(node_id)
        if isinstance(node, EmergenceNode):
            return AgentNode(node)
        return None

    def get_agents(self) -> List[AgentNode]:
        return [
            AgentNode(node)
            for node in self.graph.nodes.values()
            if isinstance(node, EmergenceNode)
        ]

    def spawn_dynamic_agent(
        self, 
        role: str, 
        initial_skills: List[str], 
        initial_tools: List[str], 
        parent_id: Optional[str] = None, 
        emergence_boost: float = 0.1
    ) -> str:
        """Spawns a new EmergenceNode representing a specialist agent.
        
        Links it back to its parent and logs the creation into the provenance chain.
        """
        agent_id = f"agent_{uuid.uuid4().hex[:8]}"
        
        node = EmergenceNode(
            id=agent_id,
            opinions={"main": 0.0},
            resources={"energy": 80.0},
            control_mode=ControlMode.EMERGENCE
        )
        
        # Populate agent-specific metadata
        agent = AgentNode(node)
        agent.role = role
        agent.active_skills = list(initial_skills)
        agent.available_tools = list(initial_tools)
        
        # Add to graph
        self.graph.add_node(node)
        
        # Provenance setup variables
        before_state = None
        after_state = {
            "id": agent_id,
            "role": role,
            "skills": initial_skills,
            "tools": initial_tools,
            "parent_id": parent_id
        }
        
        # Link to parent if provided
        if parent_id and parent_id in self.graph.nodes:
            # Create bidirectional trophallaxis/sharing pathways
            self.graph.add_edge(TrophallaxisEdge(source_id=parent_id, target_id=agent_id))
            self.graph.add_edge(TrophallaxisEdge(source_id=agent_id, target_id=parent_id))
            
            # Create command/influence edge
            self.graph.add_edge(AdaptiveEdge(
                source_id=parent_id, 
                target_id=agent_id, 
                edge_type=EdgeType.COMMAND,
                weight=1.5
            ))
            
            # Emergence flow edge
            self.graph.add_edge(EmergenceEdge(
                source_id=agent_id,
                target_id=parent_id,
                weight=1.0
            ))
        
        # Log mutation
        self.provenance.add_mutation(
            actor="swarm_orchestrator",
            operation="spawn_dynamic_agent",
            target=agent_id,
            before=before_state,
            after=after_state,
            meta={"emergence_boost": emergence_boost}
        )
        
        return agent_id

    def hibernate_or_kill_agent(self, node_id: str, reason: str):
        """Terminates an agent node and rewires or prunes its edges, logging to provenance."""
        if node_id not in self.graph.nodes:
            return
            
        agent = self.get_agent(node_id)
        before_state = {
            "id": node_id,
            "role": agent.role if agent else "unknown"
        }
        
        # Remove from physical graph (base_graph automatically handles edge cleanup)
        self.graph.remove_node(node_id)
        
        self.provenance.add_mutation(
            actor="swarm_orchestrator",
            operation="kill_agent",
            target=node_id,
            before=before_state,
            after=None,
            meta={"reason": reason}
        )
