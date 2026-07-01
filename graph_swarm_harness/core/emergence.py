import numpy as np
from typing import List, Dict, Any
from base_graph.primitives.graph import BaseGraph
from base_graph.primitives.node import EmergenceNode
from base_graph.core.metrics import emergence_level as base_emergence_level
from graph_swarm_harness.core.graph_state import SwarmGraphState

def calculate_swarm_emergence(swarm: SwarmGraphState) -> float:
    """Calculates the composite emergence level of the swarm, factoring in opinion cohesion and task focus."""
    agents = swarm.get_agents()
    if not agents:
        return 0.0

    # 1. Base Graph structural/temporal emergence
    base_val = base_emergence_level(swarm.graph, swarm.metrics_history)

    # 2. Agent opinion cohesion: standard deviation of "main" opinion
    opinions = [a.node.opinions.get("main", 0.0) for a in agents]
    if len(opinions) > 1:
        opinion_variance = np.var(opinions)
        opinion_cohesion = 1.0 / (1.0 + opinion_variance)
    else:
        opinion_cohesion = 1.0

    # 3. Energy reserves health (all agents above safety threshold)
    energies = [a.energy for a in agents]
    if energies:
        avg_energy = sum(energies) / len(energies)
        energy_health = min(1.0, avg_energy / 100.0)
    else:
        energy_health = 1.0

    # Composite Emergence Calculation:
    # 50% structural/temporal metrics, 30% opinion cohesion, 20% energy/homeostasis health
    composite = 0.5 * base_val + 0.3 * opinion_cohesion + 0.2 * energy_health
    return float(np.clip(composite, 0.0, 1.0))
