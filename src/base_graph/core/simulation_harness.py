import random
from typing import Any, Dict, List, Optional
from base_graph.core.hybrid_swarm import HybridControlSwarmGraph
from base_graph.primitives.node import EmergenceNode
from base_graph.types import ControlMode, EdgeType, Action, Decision
from base_graph.primitives.edge import TrophallaxisEdge

class SimulationHarness:
    def __init__(self) -> None:
        self.swarm: Optional[HybridControlSwarmGraph] = None

    def setup_trial(self, name: str, num_nodes: int = 10, topology: str = "ring") -> HybridControlSwarmGraph:
        """Sets up a clean swarm graph for a benchmarking trial."""
        self.swarm = HybridControlSwarmGraph(name=name, seed=42)
        random.seed(42)

        # 1. Add nodes with random initial opinions and energy
        for i in range(num_nodes):
            node = EmergenceNode(
                id=f"agent_{i}",
                opinions={"main": random.uniform(-1.0, 1.0)},
                resources={"energy": 60.0 + random.uniform(0.0, 40.0)},
                control_mode=ControlMode.EMERGENCE
            )
            self.swarm.graph.add_node(node)

        # 2. Add edges based on topology
        nodes_list = sorted(list(self.swarm.graph.nodes.keys()))
        if topology == "ring":
            for i in range(num_nodes):
                src = nodes_list[i]
                tgt = nodes_list[(i + 1) % num_nodes]
                # Bidirectional Trophallaxis/Sharing connections
                self.swarm.graph.add_edge(TrophallaxisEdge(source_id=src, target_id=tgt))
                self.swarm.graph.add_edge(TrophallaxisEdge(source_id=tgt, target_id=src))
        else:
            # Fully connected/clique style
            for i in range(num_nodes):
                for j in range(i + 1, num_nodes):
                    src, tgt = nodes_list[i], nodes_list[j]
                    self.swarm.graph.add_edge(TrophallaxisEdge(source_id=src, target_id=tgt))
                    self.swarm.graph.add_edge(TrophallaxisEdge(source_id=tgt, target_id=src))

        return self.swarm

    def run_trial(self, steps: int, strategy: Dict[str, Any]) -> Dict[str, Any]:
        """Runs the trial, routing node decisions through the local parameterized policy."""
        if self.swarm is None:
            raise ValueError("Swarm not setup. Call setup_trial first.")

        # Configure swarm trophallaxis parameters with candidate settings
        self.swarm.trophallaxis.sharing_rate = strategy.get("sharing_rate", 0.2)
        self.swarm.trophallaxis.safety_threshold = strategy.get("safety_threshold", 20.0)

        # Bind the parameterized local policy
        for node in self.swarm.graph.nodes.values():
            if isinstance(node, EmergenceNode):
                # Wrap policy with candidate strategy parameters
                node.policy = lambda n, space, ctx, strat=strategy: self._execute_node_policy(n, space, ctx, strat)

        emergence_levels = []
        energy_levels = []
        transfers_count = 0

        for _ in range(steps):
            res = self.swarm.hybrid_step()
            emergence_levels.append(res.health.emergence_level)
            
            # Record average energy
            energies = [n.resources.get("energy", 0.0) for n in self.swarm.graph.nodes.values() if isinstance(n, EmergenceNode)]
            if energies:
                energy_levels.append(sum(energies) / len(energies))

            transfers_count += res.active_modes.get("STIGMERGIC", 0) + res.active_modes.get("DECENTRALIZED", 0)

        # Compile report
        final_health = self.swarm.compute_swarm_health()
        
        return {
            "average_emergence": sum(emergence_levels) / len(emergence_levels) if emergence_levels else 0.0,
            "final_emergence": final_health.emergence_level,
            "final_energy_avg": energy_levels[-1] if energy_levels else 0.0,
            "total_transfers": transfers_count,
            "provenance_valid": final_health.provenance_integrity,
            "step_count": self.swarm.step_index
        }

    def _execute_node_policy(self, node: EmergenceNode, action_space: List[Action], context: Dict[str, Any], strategy: Dict[str, Any]) -> Decision:
        """Executes a local node decision based on candidate strategy parameter weights."""
        energy = node.resources.get("energy", 0.0)
        neighbors = context.get("neighbors", [])
        
        cooperation_weight = strategy.get("cooperation_weight", 0.5)
        consensus_weight = strategy.get("consensus_weight", 0.5)
        safety_threshold = strategy.get("safety_threshold", 20.0)

        # 1. Critical Survival Check (Self-Preservation)
        if energy < safety_threshold:
            return Decision(
                node_id=str(node.id),
                selected_action=Action(action_type="SEARCH_RESOURCE", parameters={}),
                confidence=0.95,
                reason=f"Survival override: energy ({energy:.1f}) is under safety threshold."
            )

        # 2. Heuristic evaluation of urgencies
        # Urgency A: Sharing energy with needy neighbors
        sharing_urgency = 0.0
        target_neighbor = None
        if neighbors and energy > safety_threshold + 15.0:
            # Find the poorest neighbor
            poorest = min(neighbors, key=lambda n: n.resources.get("energy", 100.0))
            poorest_energy = poorest.resources.get("energy", 100.0)
            if poorest_energy < energy - 20.0:
                sharing_urgency = cooperation_weight * (energy - poorest_energy) / 100.0
                target_neighbor = poorest.id

        # Urgency B: Aligning opinions to reach consensus
        consensus_urgency = 0.0
        my_opinion = node.opinions.get("main", 0.0)
        if neighbors:
            avg_opinion = sum(n.opinions.get("main", 0.0) for n in neighbors) / len(neighbors)
            consensus_urgency = consensus_weight * abs(my_opinion - avg_opinion)

        # 3. Decision Selection
        if sharing_urgency > consensus_urgency and target_neighbor:
            # Share energy
            return Decision(
                node_id=str(node.id),
                selected_action=Action(action_type="SHARE_RESOURCE", parameters={"target_id": str(target_neighbor), "amount": 10.0}),
                confidence=float(0.5 + 0.5 * sharing_urgency),
                reason=f"Sharing energy: Poorest neighbor {target_neighbor} needs support."
            )
        elif consensus_urgency > 0.05:
            # Shift opinions slightly closer to neighbors
            node.opinions["main"] = my_opinion + 0.15 * (avg_opinion - my_opinion)
            return Decision(
                node_id=str(node.id),
                selected_action=Action(action_type="CONVERGE_OPINION", parameters={}),
                confidence=float(0.5 + 0.5 * consensus_urgency),
                reason="Consensus alignment: adjusting opinions with neighbors."
            )
        else:
            # Rest and conserve
            return Decision(
                node_id=str(node.id),
                selected_action=Action(action_type="IDLE", parameters={}),
                confidence=0.5,
                reason="Homeostasis balanced: idling to conserve resources."
            )
