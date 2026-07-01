import time
import uuid
from typing import Any, Dict, List, Optional, Union
from uuid import UUID

from base_graph.types import (
    ControlMode,
    EdgeType,
    Action,
    Decision,
    SwarmStepResult,
    SwarmHealthReport,
    Checkpoint,
    ProvenanceRecord
)
from base_graph.primitives.graph import BaseGraph
from base_graph.primitives.node import EmergenceNode
from base_graph.primitives.edge import AdaptiveEdge, TrophallaxisEdge, EmergenceEdge
from base_graph.primitives.subgraph import DiffusionSubgraph, FractalSubgraph, DiffusionTrajectory
from base_graph.core.provenance import ProvenanceChain
from base_graph.core.trophallaxis import TrophallaxisProtocol
from base_graph.core.metrics import (
    spectral_gap,
    graph_diffusion_entropy,
    emergence_level,
    swarm_antifragility_index
)
from base_graph.utils.serialization import serialize_state, deserialize_state

class HybridControlSwarmGraph:
    def __init__(self, name: str = "swarm-001", seed: Optional[int] = None) -> None:
        self.name = name
        self.seed = seed
        self.graph = BaseGraph()
        
        # Subgraphs sharing core node references
        self.diffusion_subgraph = DiffusionSubgraph(self.graph)
        self.fractal_subgraph = FractalSubgraph(self.graph)
        
        # Core services
        self.provenance = ProvenanceChain()
        self.trophallaxis = TrophallaxisProtocol()
        
        self.step_index = 0
        self.metrics_history: List[Dict[str, Any]] = []
        self.skills: Dict[str, Any] = {}

    def set_control_mode(self, mode: Union[ControlMode, Dict[str, ControlMode]]) -> None:
        """Globally or per-node sets the control mode, logging changes in the provenance chain."""
        before_state = {nid: n.control_mode.value for nid, n in self.graph.nodes.items() if isinstance(n, EmergenceNode)}
        
        if isinstance(mode, ControlMode):
            for node in self.graph.nodes.values():
                if isinstance(node, EmergenceNode):
                    node.control_mode = mode
        elif isinstance(mode, dict):
            for nid, m in mode.items():
                node = self.graph.nodes.get(nid)
                if isinstance(node, EmergenceNode):
                    node.control_mode = m
                    
        after_state = {nid: n.control_mode.value for nid, n in self.graph.nodes.items() if isinstance(n, EmergenceNode)}
        
        self.provenance.add_mutation(
            actor="operator",
            operation="set_control_mode",
            target=self.name,
            before=before_state,
            after=after_state,
            meta={"global": isinstance(mode, ControlMode)}
        )

    def hybrid_step(self, global_context: Optional[Dict[str, Any]] = None) -> SwarmStepResult:
        """Executes one unified swarm iteration, routing decisions and running homeostasis/stigmergy."""
        if global_context is None:
            global_context = {}
            
        self.step_index += 1
        decisions: Dict[str, Decision] = {}
        active_modes: Dict[str, int] = {m.value: 0 for m in ControlMode}
        
        # 1. Collect contexts and step nodes
        node_ids_sorted = sorted(list(self.graph.nodes.keys()))
        
        # Record before state for step provenance bundle
        before_nodes_state = {
            nid: {
                "resources": node.resources.copy() if hasattr(node, "resources") else {},
                "opinions": node.opinions.copy() if hasattr(node, "opinions") else {}
            } for nid, node in self.graph.nodes.items()
        }

        # Step each node
        for nid in node_ids_sorted:
            node = self.graph.nodes[nid]
            if not isinstance(node, EmergenceNode):
                continue
                
            active_modes[node.control_mode.value] += 1
            
            # Gathers node environment
            local_edges = [
                e for e in self.graph.edges.values()
                if e.source_id == nid or e.target_id == nid
            ]
            neighbors = self.graph.get_neighbors(nid)
            
            # Commands for hierarchical mode
            incoming_commands = []
            if node.control_mode == ControlMode.HIERARCHICAL:
                # Find command type incoming edges
                for edge in local_edges:
                    if edge.target_id == nid and edge.edge_type == EdgeType.COMMAND:
                        incoming_commands.append({
                            "source": edge.source_id,
                            "type": edge.metadata.get("command_type", "IDLE"),
                            "params": edge.metadata.get("command_params", {})
                        })

            context = {
                "global_time": self.step_index,
                "neighbors": neighbors,
                "local_edges": [
                    {
                        "id": e.id,
                        "source_id": e.source_id,
                        "target_id": e.target_id,
                        "weight": e.weight,
                        "type": e.edge_type.value,
                        "pheromone": e.metadata.get("pheromone", 0.0)
                    } for e in local_edges
                ],
                "incoming_commands": incoming_commands,
                **global_context
            }
            
            action = node.local_step(context)
            
            # Record decision mapping
            decisions[nid] = Decision(
                node_id=nid,
                selected_action=action,
                confidence=node.local_memory.get("last_confidence", 0.8),
                reason=node.local_memory.get("last_decision_reason", "Default execution")
            )

        # 2. Run Stigmergy update (evaporate/decay pheromones and process deposits)
        for edge in self.graph.edges.values():
            if isinstance(edge, EmergenceEdge):
                # Evaporate
                edge.decay_flow(decay_rate=0.05)
                # Apply deposits
                for node in self.graph.nodes.values():
                    if isinstance(node, EmergenceNode):
                        deposits = node.local_memory.get("stigmergy_deposits", [])
                        for dep in deposits:
                            if dep.get("edge_id") == edge.id:
                                edge.emergence_flow += dep.get("intensity", 0.0)
                                # Strengthen edge
                                edge.update_weight(
                                    delta=0.1 * dep.get("intensity", 0.0),
                                    reason="stigmergic reinforcement"
                                )

        # Clear stigmergy deposits for next round
        for node in self.graph.nodes.values():
            if isinstance(node, EmergenceNode):
                node.local_memory["stigmergy_deposits"] = []

        # 3. Run Trophallaxis resource sharing and metabolism
        transfers = self.trophallaxis.distribute_resources(self.graph)
        starving = self.trophallaxis.simulate_metabolism(self.graph, cost=1.0)
        
        # 4. Evaluate Swarm Health metrics
        health = self.compute_swarm_health()
        
        # Record after state
        after_nodes_state = {
            nid: {
                "resources": node.resources.copy() if hasattr(node, "resources") else {},
                "opinions": node.opinions.copy() if hasattr(node, "opinions") else {}
            } for nid, node in self.graph.nodes.items()
        }
        
        # Commit single delta for entire swarm step transitions to provenance
        self.provenance.add_mutation(
            actor="swarm_engine",
            operation="hybrid_step",
            target=str(self.step_index),
            before=before_nodes_state,
            after=after_nodes_state,
            meta={
                "transfers_executed": transfers,
                "starving_count": len(starving),
                "active_modes": active_modes
            }
        )

        # Update metrics history
        serialized_history = {
            "step": self.step_index,
            "health": health.model_dump(),
            "nodes": [
                {
                    "id": nid,
                    "resources": node.resources.copy() if hasattr(node, "resources") else {},
                    "opinions": node.opinions.copy() if hasattr(node, "opinions") else {},
                    "mode": node.control_mode.value if hasattr(node, "control_mode") else "BASE"
                } for nid, node in self.graph.nodes.items()
            ]
        }
        self.metrics_history.append(serialized_history)
        
        return SwarmStepResult(
            step_index=self.step_index,
            active_modes=active_modes,
            decisions=decisions,
            health=health,
            provenance_hash=self.provenance.get_latest_hash()
        )

    def adaptive_hybrid_decision(self, node_id: str, context: Dict[str, Any]) -> Decision:
        """Performs expert-style gating or emergency command injection prior to stepping."""
        node = self.graph.nodes.get(node_id)
        if not isinstance(node, EmergenceNode):
            raise ValueError(f"Node {node_id} is not an EmergenceNode")

        # Let's inspect human override setting
        human_command = context.get("human_override_command")
        if human_command:
            # Human override escape hatch: enforce decision instantly
            action = Action(
                action_type=human_command.get("type", "IDLE"),
                parameters=human_command.get("params", {})
            )
            return Decision(
                node_id=node_id,
                selected_action=action,
                confidence=1.0,
                reason="HUMAN OVERRIDE ABSOLUTE ESCAPE HATCH"
            )

        # Standard routing
        return node.decide(
            action_space=[
                Action(action_type="IDLE", parameters={}),
                Action(action_type="CONVERGE_OPINION", parameters={})
            ],
            context=context
        )

    def compute_swarm_health(self) -> SwarmHealthReport:
        """Aggregates metrics for spectral properties, entropy, balance, and cryptographic chain validity."""
        n = len(self.graph.nodes)
        
        # Calculate components
        gap = spectral_gap(self.graph)
        antifragility = swarm_antifragility_index(self.graph)
        
        # Consensus entropy (DeGroot diffusion opinion alignment)
        op_vals = []
        for node in self.graph.nodes.values():
            if isinstance(node, EmergenceNode):
                op_vals.extend(node.opinions.values())
            else:
                op_vals.append(node.state.get("opinion", 0.0))
                
        # Scale to range [0, 1]
        op_norm = [v + 1.0 for v in op_vals] if op_vals else [0.0]
        entropy_val = graph_diffusion_entropy(
            DiffusionTrajectory(model="opinion", steps_run=0, entropy_curve=[self.diffusion_subgraph._compute_opinion_entropy({str(i): v for i, v in enumerate(op_vals)})])
        ) if op_vals else 0.5
        
        # Resource balance: variance of energies
        energies = []
        for node in self.graph.nodes.values():
            if isinstance(node, EmergenceNode):
                energies.append(node.resources.get("energy", 0.0))
            else:
                energies.append(node.state.get("energy", 0.0))
                
        resource_balance = 1.0
        if energies:
            mean_energy = sum(energies) / len(energies)
            variance = sum((e - mean_energy) ** 2 for e in energies) / len(energies)
            # Homeostasis scale: lower variance -> higher balance index
            resource_balance = 1.0 / (1.0 + 0.001 * variance)

        # Provenance verification check
        chain_valid = self.provenance.verify_chain()
        
        # Composite emergence level
        e_level = emergence_level(self.graph, self.metrics_history)

        return SwarmHealthReport(
            emergence_level=e_level,
            spectral_gap=gap,
            diffusion_entropy=entropy_val,
            resource_balance=resource_balance,
            provenance_integrity=chain_valid,
            antifragility_score=antifragility,
            node_count=n,
            edge_count=len(self.graph.edges)
        )

    def checkpoint(self) -> Checkpoint:
        """Returns a snapshot of the graph nodes, edges, and provenance trail."""
        nodes_state = []
        for nid, node in self.graph.nodes.items():
            if isinstance(node, EmergenceNode):
                n_dict = {
                    "id": str(node.id),
                    "resources": node.resources.copy(),
                    "opinions": node.opinions.copy(),
                    "goals": node.goals.copy(),
                    "control_mode": node.control_mode.value,
                    "local_memory": node.local_memory.copy(),
                    "state": node.state.copy(),
                    "metadata": node.metadata.copy()
                }
            else:
                n_dict = {
                    "id": str(node.id),
                    "state": node.state.copy(),
                    "metadata": node.metadata.copy()
                }
            nodes_state.append(n_dict)

        edges_state = []
        for eid, edge in self.graph.edges.items():
            edges_state.append({
                "source_id": edge.source_id,
                "target_id": edge.target_id,
                "weight": edge.weight,
                "edge_type": edge.edge_type.value,
                "strength": edge.strength,
                "last_updated": edge.last_updated,
                "usage_count": edge.usage_count,
                "metadata": edge.metadata.copy(),
                "class_name": edge.__class__.__name__
            })

        provenance_chain_serialized = [
            rec.model_dump() for rec in self.provenance.chain
        ]

        state_hash = self.provenance.compute_state_sha256(self.graph.nodes, self.graph.edges)

        return Checkpoint(
            timestamp=time.time(),
            checkpoint_id=str(uuid.uuid4()),
            state_hash=state_hash,
            nodes_state=nodes_state,
            edges_state=edges_state,
            provenance_chain=provenance_chain_serialized
        )

    def restore(self, checkpoint: Union[Checkpoint, str]) -> None:
        """Restores the swarm state to a previous Checkpoint, validating integrity."""
        if isinstance(checkpoint, str):
            # De-serialize Checkpoint object
            ckpt_dict = deserialize_state(checkpoint)
            ckpt = Checkpoint.model_validate(ckpt_dict)
        else:
            ckpt = checkpoint

        # Re-build graph primitives
        new_graph = BaseGraph()
        
        for n_dict in ckpt.nodes_state:
            nid = n_dict["id"]
            if "control_mode" in n_dict:
                node = EmergenceNode(
                    id=nid,
                    state=n_dict["state"],
                    metadata=n_dict["metadata"],
                    local_memory=n_dict["local_memory"],
                    resources=n_dict["resources"],
                    opinions=n_dict["opinions"],
                    goals=n_dict["goals"],
                    control_mode=ControlMode(n_dict["control_mode"])
                )
            else:
                node = BaseNode(
                    id=nid,
                    state=n_dict["state"],
                    metadata=n_dict["metadata"]
                )
            new_graph.add_node(node)

        for e_dict in ckpt.edges_state:
            class_name = e_dict.get("class_name", "AdaptiveEdge")
            etype = EdgeType(e_dict["edge_type"])
            
            if class_name == "TrophallaxisEdge":
                edge = TrophallaxisEdge(
                    source_id=e_dict["source_id"],
                    target_id=e_dict["target_id"],
                    weight=e_dict["weight"],
                    strength=e_dict["strength"],
                    last_updated=e_dict["last_updated"],
                    usage_count=e_dict["usage_count"],
                    metadata=e_dict["metadata"]
                )
            elif class_name == "EmergenceEdge":
                edge = EmergenceEdge(
                    source_id=e_dict["source_id"],
                    target_id=e_dict["target_id"],
                    weight=e_dict["weight"],
                    strength=e_dict["strength"],
                    last_updated=e_dict["last_updated"],
                    usage_count=e_dict["usage_count"],
                    metadata=e_dict["metadata"]
                )
            else:
                edge = AdaptiveEdge(
                    source_id=e_dict["source_id"],
                    target_id=e_dict["target_id"],
                    weight=e_dict["weight"],
                    edge_type=etype,
                    strength=e_dict["strength"],
                    last_updated=e_dict["last_updated"],
                    usage_count=e_dict["usage_count"],
                    metadata=e_dict["metadata"]
                )
            new_graph.add_edge(edge)

        # Restore graph reference
        self.graph = new_graph
        self.diffusion_subgraph = DiffusionSubgraph(self.graph)
        self.fractal_subgraph = FractalSubgraph(self.graph)

        # Restore provenance chain
        self.provenance = ProvenanceChain()
        for rec_dict in ckpt.provenance_chain:
            self.provenance.chain.append(ProvenanceRecord.model_validate(rec_dict))
        
        if self.provenance.chain:
            self.provenance._current_hash = self.provenance.chain[-1].current_hash
        else:
            self.provenance._current_hash = "0" * 64
            
        # Verify integrity
        restored_hash = self.provenance.compute_state_sha256(self.graph.nodes, self.graph.edges)
        if restored_hash != ckpt.state_hash:
            raise ValueError(
                f"State integrity mismatch on restore! Checkpoint state hash: {ckpt.state_hash}, restored: {restored_hash}"
            )

    def register_skill_extension(self, skill_name: str, extension: Any) -> None:
        """Registers a higher-order swarm skill extension directly into orchestrator hooks."""
        self.skills[skill_name] = extension
        
        # Log skill injection
        self.provenance.add_mutation(
            actor="operator",
            operation="register_skill_extension",
            target=skill_name,
            before=None,
            after=skill_name,
            meta={"skill_class": extension.__class__.__name__}
        )
