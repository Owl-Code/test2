from typing import Any, Dict, List, Optional
from base_graph.core.hybrid_swarm import HybridControlSwarmGraph
from base_graph.types import SwarmStepResult

class SimulationEngine:
    def __init__(self, swarm: HybridControlSwarmGraph) -> None:
        self.swarm = swarm

    def run_steps(self, steps: int, global_context: Optional[Dict[str, Any]] = None) -> List[SwarmStepResult]:
        """Runs the simulation for a specified number of steps, yielding step results."""
        results = []
        for _ in range(steps):
            res = self.swarm.hybrid_step(global_context)
            results.append(res)
        return results

    def run_diffusion_on_subgraph(self, model: str = "opinion", steps: int = 50, params: Optional[Dict[str, Any]] = None) -> Any:
        """Invokes diffusion processes on opinion, heat, or epidemiological sub-matrices."""
        return self.swarm.diffusion_subgraph.run_diffusion(
            model=model,
            steps=steps,
            params=params
        )
