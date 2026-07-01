from typing import Dict, Any, List
from base_graph.types import ControlMode, SwarmHealthReport
from graph_swarm_harness.core.graph_state import SwarmGraphState

class HybridControlManager:
    """Manages adaptive control mode switching for the graph swarm.
    
    Dynamically re-allocates control modes based on emergence, resource distribution,
    and consensus/polarity signals.
    """
    
    def __init__(self, target_cohesion: float = 0.85, emergency_energy_threshold: float = 35.0):
        self.target_cohesion = target_cohesion
        self.emergency_energy_threshold = emergency_energy_threshold
        self.mode_history: List[str] = []

    def evaluate_and_adapt(self, swarm: SwarmGraphState, health: SwarmHealthReport) -> str:
        """Evaluates health metrics and adaptively switches node control modes if the swarm is in ADAPTIVE mode.
        
        Returns the new dominant control mode.
        """
        agents = swarm.get_agents()
        if not agents:
            return "IDLE"

        # Check if any agent has critically low energy (homeostasis stress)
        starving_count = sum(1 for a in agents if a.energy < self.emergency_energy_threshold)
        starving_ratio = starving_count / len(agents)

        # Retrieve current dominant mode
        current_modes = [a.node.control_mode for a in agents]
        dominant_mode = max(set(current_modes), key=current_modes.count)

        # Heuristic rules for adaptive switching:
        # 1. Critical Homeostasis Stress (high starvation ratio) -> Force HIERARCHICAL command mode 
        #    to centralize search/collection rules or direct resources immediately.
        if starving_ratio > 0.3:
            target_mode = ControlMode.HIERARCHICAL
            reason = f"Starvation ratio high ({starving_ratio:.2f}); enforcing HIERARCHICAL stabilization"
            
        # 2. Opinion polarization is high, but resources are fine -> Shift to DECENTRALIZED
        #    to let local bounded confidence consensus rules settle the opinions.
        elif health.diffusion_entropy > 0.75:
            target_mode = ControlMode.DECENTRALIZED
            reason = f"High diffusion entropy ({health.diffusion_entropy:.2f}); enabling DECENTRALIZED consensus"
            
        # 3. Swarm is highly cohesive and energy balanced -> Shift to STIGMERGIC / EMERGENCE
        #    for autonomous self-organization and stigmergic edge routing.
        elif health.emergence_level > 0.7:
            target_mode = ControlMode.EMERGENCE
            reason = f"High emergence level ({health.emergence_level:.2f}); enabling EMERGENCE mode"
        
        else:
            # Maintain current or fallback to EMERGENCE
            target_mode = dominant_mode
            reason = "Swarm metrics within normal bounds; maintaining current regime"

        # Apply mode transitions if changed
        any_changed = False
        mode_changes = {}
        
        for agent in agents:
            if agent.node.control_mode != target_mode:
                agent.node.control_mode = target_mode
                mode_changes[agent.id] = target_mode.value
                any_changed = True

        if any_changed:
            swarm.provenance.add_mutation(
                actor="hybrid_control_manager",
                operation="adaptive_mode_switch",
                target=swarm.name,
                before={"dominant_mode": dominant_mode.value},
                after={"dominant_mode": target_mode.value, "changes": mode_changes},
                meta={"reason": reason, "starving_ratio": starving_ratio, "emergence_level": health.emergence_level}
            )

        self.mode_history.append(target_mode.value)
        return target_mode.value
