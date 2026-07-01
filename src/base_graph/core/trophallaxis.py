from typing import Any, Dict, List
from base_graph.primitives.graph import BaseGraph
from base_graph.primitives.edge import TrophallaxisEdge
from base_graph.primitives.node import EmergenceNode

class TrophallaxisProtocol:
    def __init__(self, resource_type: str = "energy", sharing_rate: float = 0.2, max_flow: float = 20.0, safety_threshold: float = 20.0) -> None:
        self.resource_type = resource_type
        self.sharing_rate = sharing_rate
        self.max_flow = max_flow
        self.safety_threshold = safety_threshold

    def simulate_metabolism(self, graph: BaseGraph, cost: float = 1.0) -> List[Dict[str, Any]]:
        """Simulates internal energy consumption of nodes.
        
        Returns a list of warnings for starving nodes (energy < safety_threshold).
        """
        starving_nodes = []
        for nid, node in graph.nodes.items():
            if isinstance(node, EmergenceNode):
                current = node.resources.get(self.resource_type, 0.0)
                # Reduce by metabolic cost
                new_val = max(0.0, current - cost)
                node.resources[self.resource_type] = new_val
                
                # Check for critical status
                if new_val < self.safety_threshold:
                    starving_nodes.append({
                        "node_id": nid,
                        "resource": self.resource_type,
                        "current_level": new_val
                    })
                    node.local_memory["starving"] = True
                else:
                    node.local_memory.pop("starving", None)
        return starving_nodes

    def distribute_resources(self, graph: BaseGraph) -> int:
        """Executes trophallaxis sharing across all TrophallaxisEdges in the graph.
        
        Returns the number of successful transfers.
        """
        transfers_executed = 0
        
        # Sort edges by source_id to maintain determinism
        troph_edges = [
            edge for edge in graph.edges.values()
            if isinstance(edge, TrophallaxisEdge)
        ]
        troph_edges.sort(key=lambda e: e.id)
        
        for edge in troph_edges:
            src_node = graph.nodes.get(edge.source_id)
            tgt_node = graph.nodes.get(edge.target_id)
            
            if not isinstance(src_node, EmergenceNode) or not isinstance(tgt_node, EmergenceNode):
                continue
                
            src_val = src_node.resources.get(self.resource_type, 0.0)
            tgt_val = tgt_node.resources.get(self.resource_type, 0.0)
            
            # Transfer only if source is richer and has energy above safety threshold
            if src_val > tgt_val and src_val > self.safety_threshold:
                # Compute potential transfer amount
                diff = src_val - tgt_val
                amount = min(self.max_flow, self.sharing_rate * diff)
                
                if amount > 0.1:
                    # Establish transfer safety parameters on node
                    src_node.local_memory["homeostasis_safety_threshold"] = self.safety_threshold
                    success = edge.transfer(src_node, tgt_node, self.resource_type, amount)
                    if success:
                        transfers_executed += 1
                        
        return transfers_executed
