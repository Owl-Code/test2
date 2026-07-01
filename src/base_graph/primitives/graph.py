import math
from typing import Dict, List, Optional, Set, Tuple, Union, Any
from uuid import UUID

from base_graph.primitives.node import BaseNode
from base_graph.primitives.edge import AdaptiveEdge
from base_graph.types import EdgeType

try:
    import numpy as np
except ImportError:
    np = None  # type: ignore

class BaseGraph:
    def __init__(self) -> None:
        self.nodes: Dict[str, BaseNode] = {}
        self.edges: Dict[str, AdaptiveEdge] = {}
        # Adjacency structures for speed
        self._adjacency_list: Dict[str, Set[str]] = {}
        self._reverse_adjacency_list: Dict[str, Set[str]] = {}

    def add_node(self, node: BaseNode) -> None:
        """Adds a node to the graph and registers adjacency slots."""
        node_id = str(node.id)
        self.nodes[node_id] = node
        self._adjacency_list.setdefault(node_id, set())
        self._reverse_adjacency_list.setdefault(node_id, set())

    def remove_node(self, node_id: str) -> None:
        """Removes a node and all of its associated edges from the graph."""
        if node_id not in self.nodes:
            return
        
        # Remove edges originating from or targeting this node
        edges_to_remove = [
            edge_id for edge_id, edge in self.edges.items()
            if edge.source_id == node_id or edge.target_id == node_id
        ]
        for edge_id in edges_to_remove:
            self.remove_edge(edge_id)
            
        self.nodes.pop(node_id, None)
        self._adjacency_list.pop(node_id, None)
        self._reverse_adjacency_list.pop(node_id, None)

    def add_edge(self, edge: AdaptiveEdge) -> None:
        """Adds or updates an edge, registering source and target nodes if not present."""
        if edge.source_id not in self.nodes:
            # Create a default BaseNode
            self.add_node(BaseNode(id=edge.source_id))
        if edge.target_id not in self.nodes:
            self.add_node(BaseNode(id=edge.target_id))
            
        self.edges[edge.id] = edge
        self._adjacency_list[edge.source_id].add(edge.target_id)
        self._reverse_adjacency_list[edge.target_id].add(edge.source_id)

    def remove_edge(self, edge_id: str) -> None:
        """Removes an edge from the graph."""
        if edge_id not in self.edges:
            return
        edge = self.edges.pop(edge_id)
        
        # Update adjacency lists
        if edge.source_id in self._adjacency_list:
            self._adjacency_list[edge.source_id].discard(edge.target_id)
        if edge.target_id in self._reverse_adjacency_list:
            self._reverse_adjacency_list[edge.target_id].discard(edge.source_id)

    def rewire(self, edge_id: str, new_target_id: str) -> None:
        """Changes the target node of an existing edge to new_target_id."""
        if edge_id not in self.edges:
            return
        edge = self.edges[edge_id]
        
        # Remove old link
        self._adjacency_list[edge.source_id].discard(edge.target_id)
        self._reverse_adjacency_list[edge.target_id].discard(edge.source_id)
        
        # Update target
        edge.target_id = new_target_id
        if new_target_id not in self.nodes:
            self.add_node(BaseNode(id=new_target_id))
            
        # Add new link
        self._adjacency_list[edge.source_id].add(new_target_id)
        self._reverse_adjacency_list[new_target_id].add(edge.source_id)
        
        # Re-key edge in dict
        self.edges.pop(edge_id)
        self.edges[edge.id] = edge

    def get_neighbors(self, node_id: str, edge_type_filter: Optional[EdgeType] = None) -> List[BaseNode]:
        """Gets all outgoing neighbor nodes of node_id, optionally filtered by edge type."""
        if node_id not in self._adjacency_list:
            return []
        
        targets = self._adjacency_list[node_id]
        neighbors = []
        for tgt in targets:
            edge_key = f"{node_id}->{tgt}"
            edge = self.edges.get(edge_key)
            if edge:
                if edge_type_filter is None or edge.edge_type == edge_type_filter:
                    if tgt in self.nodes:
                        neighbors.append(self.nodes[tgt])
        return neighbors

    def to_adjacency_matrix(self, sparse: bool = False) -> Union[Any, List[List[float]]]:
        """Returns the adjacency matrix representation of the graph.
        
        Uses NumPy if available, else returns a nested Python list.
        """
        node_ids = sorted(list(self.nodes.keys()))
        n = len(node_ids)
        id_map = {node_id: idx for idx, node_id in enumerate(node_ids)}
        
        if np is not None:
            adj = np.zeros((n, n), dtype=np.float64)
            for edge in self.edges.values():
                if edge.source_id in id_map and edge.target_id in id_map:
                    adj[id_map[edge.source_id], id_map[edge.target_id]] = edge.weight
            return adj
        else:
            adj_list = [[0.0] * n for _ in range(n)]
            for edge in self.edges.values():
                if edge.source_id in id_map and edge.target_id in id_map:
                    adj_list[id_map[edge.source_id]][id_map[edge.target_id]] = edge.weight
            return adj_list

    def laplacian_matrix(self, normalized: bool = True) -> Union[Any, List[List[float]]]:
        """Computes the Laplacian matrix of the graph.
        
        Uses NumPy if available, else returns a nested Python list.
        """
        node_ids = sorted(list(self.nodes.keys()))
        n = len(node_ids)
        if n == 0:
            return np.zeros((0, 0)) if np is not None else []
            
        adj = self.to_adjacency_matrix()
        
        if np is not None:
            adj = np.array(adj, dtype=np.float64)
            # Degrees are sum of rows (outgoing + incoming undirected, or outgoing for directed)
            # For Laplacian, we treat it as undirected by symmetrizing the adj matrix
            sym_adj = 0.5 * (adj + adj.T)
            degrees = np.sum(sym_adj, axis=1)
            
            if normalized:
                # L = I - D^{-1/2} A D^{-1/2}
                d_inv_sqrt = np.zeros(n)
                for i in range(n):
                    if degrees[i] > 0:
                        d_inv_sqrt[i] = 1.0 / np.sqrt(degrees[i])
                D_inv_sqrt = np.diag(d_inv_sqrt)
                L = np.eye(n) - D_inv_sqrt @ sym_adj @ D_inv_sqrt
                return L
            else:
                D = np.diag(degrees)
                L = D - sym_adj
                return L
        else:
            # Pure Python implementation
            n_ids = len(node_ids)
            # Symmetrize adjacency matrix
            adj_raw = adj
            sym_adj_list = [[0.0] * n for _ in range(n)]
            for i in range(n):
                for j in range(n):
                    val = 0.5 * (adj_raw[i][j] + adj_raw[j][i]) # type: ignore
                    sym_adj_list[i][j] = val
                    
            degrees_list = [sum(row) for row in sym_adj_list]
            
            if normalized:
                # L[i][j] = 1 if i == j (and degree[i] > 0) else -A[i][j] / sqrt(deg[i]*deg[j])
                L_list = [[0.0] * n for _ in range(n)]
                for i in range(n):
                    L_list[i][i] = 1.0 if degrees_list[i] > 0 else 0.0
                    for j in range(n):
                        if i != j and sym_adj_list[i][j] > 0:
                            deg_product = degrees_list[i] * degrees_list[j]
                            if deg_product > 0:
                                L_list[i][j] = -sym_adj_list[i][j] / math.sqrt(deg_product)
                return L_list
            else:
                L_list = [[0.0] * n for _ in range(n)]
                for i in range(n):
                    L_list[i][i] = degrees_list[i]
                    for j in range(n):
                        if i != j:
                            L_list[i][j] = -sym_adj_list[i][j]
                return L_list

    def subgraph(self, node_ids: List[str]) -> "BaseGraph":
        """Returns a copy of the graph containing only the specified nodes and edges between them."""
        sub = BaseGraph()
        nodes_set = set(node_ids)
        for nid in node_ids:
            if nid in self.nodes:
                sub.add_node(self.nodes[nid])
                
        for edge in self.edges.values():
            if edge.source_id in nodes_set and edge.target_id in nodes_set:
                sub.add_edge(edge)
        return sub

    def dynamic_restructure(self, rules: Dict[str, Any]) -> None:
        """Adapts the graph structure at runtime based on defined rules.
        
        Example rules:
          - "rewire_low_weight": float threshold
          - "prune_weak_edges": float threshold
        """
        prune_threshold = rules.get("prune_weak_edges")
        if prune_threshold is not None:
            weak_edges = [
                eid for eid, edge in self.edges.items()
                if edge.weight < prune_threshold
            ]
            for eid in weak_edges:
                self.remove_edge(eid)
                
        rewire_threshold = rules.get("rewire_low_weight")
        if rewire_threshold is not None:
            low_edges = [
                edge for edge in self.edges.values()
                if edge.weight < rewire_threshold
            ]
            for edge in low_edges:
                # Find a random node with higher energy or state and reconnect to it
                eligible_nodes = [
                    nid for nid in self.nodes.keys()
                    if nid != edge.source_id and nid != edge.target_id
                ]
                if eligible_nodes:
                    # Deterministically pick first eligible (or sort by ID to be deterministic)
                    eligible_nodes.sort()
                    new_tgt = eligible_nodes[0]
                    self.rewire(edge.id, new_tgt)
