import hashlib
import json
import time
from typing import Any, Dict, List, Optional
from base_graph.types import ProvenanceRecord, StateDelta

class ProvenanceChain:
    def __init__(self) -> None:
        self.chain: List[ProvenanceRecord] = []
        self._current_hash: str = "0" * 64

    def add_mutation(self, actor: str, operation: str, target: str, before: Any, after: Any, meta: Optional[Dict[str, Any]] = None) -> ProvenanceRecord:
        """Adds a state mutation record to the chain and computes its linked cryptographic hash."""
        delta = StateDelta(
            timestamp=time.time(),
            actor=actor,
            operation=operation,
            target=target,
            before=before,
            after=after,
            meta=meta or {}
        )
        
        index = len(self.chain)
        
        # SHA256 (previous_hash + delta serialized)
        payload = f"{self._current_hash}:{json.dumps(delta.model_dump(mode='json'), sort_keys=True)}"
        new_hash = hashlib.sha256(payload.encode("utf-8")).hexdigest()
        
        record = ProvenanceRecord(
            index=index,
            timestamp=delta.timestamp,
            delta=delta,
            previous_hash=self._current_hash,
            current_hash=new_hash
        )
        
        self.chain.append(record)
        self._current_hash = new_hash
        return record

    def get_latest_hash(self) -> str:
        return self._current_hash

    def verify_chain(self) -> bool:
        """Cryptographically verifies the integrity of the chain.
        
        Returns True if the hash links are unbroken, otherwise False.
        """
        expected_prev_hash = "0" * 64
        for idx, record in enumerate(self.chain):
            if record.index != idx:
                return False
            if record.previous_hash != expected_prev_hash:
                return False
                
            payload = f"{expected_prev_hash}:{json.dumps(record.delta.model_dump(mode='json'), sort_keys=True)}"
            recomputed_hash = hashlib.sha256(payload.encode("utf-8")).hexdigest()
            
            if record.current_hash != recomputed_hash:
                return False
                
            expected_prev_hash = record.current_hash
            
        return True

    def compute_state_sha256(self, nodes: Dict[str, Any], edges: Dict[str, Any]) -> str:
        """Computes a deterministic hash of the current physical state of the nodes and edges.
        
        This enables verifying that the physical graph matches the audit trail.
        """
        # Node states normalized
        serialized_nodes = []
        for nid in sorted(nodes.keys()):
            node = nodes[nid]
            # Handle both BaseNode object and raw dict
            if hasattr(node, "resources"):
                node_dict = {
                    "id": str(node.id),
                    "resources": node.resources,
                    "opinions": node.opinions,
                    "control_mode": node.control_mode.value,
                    "state": node.state
                }
            else:
                node_dict = node
            serialized_nodes.append(node_dict)

        # Edge states normalized
        serialized_edges = []
        for eid in sorted(edges.keys()):
            edge = edges[eid]
            if hasattr(edge, "weight"):
                edge_dict = {
                    "id": edge.id,
                    "weight": edge.weight,
                    "strength": edge.strength,
                    "type": edge.edge_type.value
                }
            else:
                edge_dict = edge
            serialized_edges.append(edge_dict)

        state_payload = {
            "nodes": serialized_nodes,
            "edges": serialized_edges
        }
        
        serialized_state = json.dumps(state_payload, sort_keys=True)
        return hashlib.sha256(serialized_state.encode("utf-8")).hexdigest()

    def export_mcp_packet(self) -> Dict[str, Any]:
        """Exports the chain state in a standardized MCP-compatible context packet format."""
        return {
            "schema": "base_graph/provenance_chain/v1",
            "provenance_chain_length": len(self.chain),
            "head_hash": self._current_hash,
            "chain_valid": self.verify_chain(),
            "records": [r.model_dump(mode="json") for r in self.chain[-20:]]  # Include last 20 records for context
        }
