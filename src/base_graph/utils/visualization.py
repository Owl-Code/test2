import math
from typing import List, TYPE_CHECKING

if TYPE_CHECKING:
    from base_graph.core.hybrid_swarm import HybridControlSwarmGraph

from base_graph.primitives.node import EmergenceNode

class TerminalDashboard:
    @staticmethod
    def render(swarm: "HybridControlSwarmGraph") -> str:
        """Renders a visual ASCII dashboard of the current swarm state."""
        health = swarm.compute_swarm_health()
        
        # 1. Title Banner
        lines = []
        lines.append("=" * 70)
        lines.append(f" SWARM MONITOR: {swarm.name.upper()} | Step: {swarm.step_index:03d}")
        lines.append("=" * 70)
        
        # 2. Swarm Health indicators
        def draw_bar(val: float, width: int = 15) -> str:
            val = max(0.0, min(1.0, val))
            filled = int(round(val * width))
            return "#" * filled + "." * (width - filled)
            
        lines.append(f"  Emergence Level:   [{draw_bar(health.emergence_level)}] {health.emergence_level:.3f}")
        lines.append(f"  Spectral Gap:       [{draw_bar(health.spectral_gap)}] {health.spectral_gap:.3f}")
        lines.append(f"  Diffusion Entropy:  [{draw_bar(health.diffusion_entropy)}] {health.diffusion_entropy:.3f}")
        lines.append(f"  Resource Balance:   [{draw_bar(health.resource_balance)}] {health.resource_balance:.3f}")
        lines.append(f"  Antifragility Index:[{draw_bar(health.antifragility_score)}] {health.antifragility_score:.3f}")
        lines.append(f"  Provenance Health:  [ {'VALID' if health.provenance_integrity else 'BROKEN'} ] (Hash: {health.metadata.get('head_hash', swarm.provenance.get_latest_hash()[:8])}...)")
        lines.append("-" * 70)
        
        # 3. Node list
        lines.append("  NODES DISTRIBUTION:")
        nodes_sorted = sorted(list(swarm.graph.nodes.items()))
        
        # Group printing for spacing
        for nid, node in nodes_sorted[:10]: # Print up to 10 nodes for space
            if isinstance(node, EmergenceNode):
                energy = node.resources.get("energy", 0.0)
                energy_bar = draw_bar(energy / 100.0, 10)
                
                # opinion values display
                ops_str = ", ".join(f"{topic}:{val:+.2f}" for topic, val in node.opinions.items())
                ops_disp = f"({ops_str})" if ops_str else ""
                
                mode_str = node.control_mode.value[:4]
                starving_indicator = "[!] STARVE" if node.local_memory.get("starving") else "          "
                
                lines.append(f"   Node [{nid[:8]}...] Mode:{mode_str} | Energy: {energy:5.1f} [{energy_bar}] | {starving_indicator} {ops_disp}")
            else:
                lines.append(f"   Node [{nid[:8]}...] Base Node | State: {node.state}")
                
        if len(nodes_sorted) > 10:
            lines.append(f"   ... and {len(nodes_sorted) - 10} other nodes.")
        lines.append("-" * 70)
        
        # 4. Edges list
        lines.append("  ACTIVE EDGES (Top 6 by usage):")
        edges_sorted = sorted(list(swarm.graph.edges.values()), key=lambda e: e.usage_count, reverse=True)
        for edge in edges_sorted[:6]:
            lines.append(
                f"   Edge [{edge.source_id[:4]}... -> {edge.target_id[:4]}...] Weight: {edge.weight:.2f} | Strength: {edge.strength:.2f} | Type: {edge.edge_type.value[:5]} | Uses: {edge.usage_count}"
            )
        if len(edges_sorted) > 6:
            lines.append(f"   ... and {len(edges_sorted) - 6} other edges.")
        lines.append("-" * 70)

        # 5. Provenance entries
        lines.append("  RECENT PROVENANCE CHAIN LOGS (Last 3):")
        records = swarm.provenance.chain[-3:]
        for rec in reversed(records):
            delta = rec.delta
            lines.append(
                f"   [{rec.index:03d}] {delta.actor} -> {delta.operation} ({delta.target}) | Hash: {rec.current_hash[:8]}..."
            )
        lines.append("=" * 70)
        
        return "\n".join(lines)
