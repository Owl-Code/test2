import random
from typing import Any, Dict, List, Tuple
from base_graph.core.simulation_harness import SimulationHarness

class MetaSkillEvolver:
    def __init__(self) -> None:
        pass

    def create_random_candidate(self) -> Dict[str, Any]:
        """Generates a random parameter candidate profile."""
        return {
            "sharing_rate": round(random.uniform(0.05, 0.40), 3),
            "safety_threshold": round(random.uniform(15.0, 35.0), 1),
            "cooperation_weight": round(random.uniform(0.0, 1.0), 3),
            "consensus_weight": round(random.uniform(0.0, 1.0), 3),
            "fitness": 0.0
        }

    def evaluate_candidate(self, candidate: Dict[str, Any], steps: int = 15) -> float:
        """Runs a simulation harness trial to evaluate the candidate's fitness.
        
        Fitness is a composite: 70% final emergence level + 30% resource conservation.
        """
        harness = SimulationHarness()
        swarm = harness.setup_trial(name="evolution-trial", num_nodes=6, topology="ring")
        
        # Run trial with candidate parameters
        result = harness.run_trial(steps=steps, strategy=candidate)
        
        # Calculate composite fitness
        emergence = result["final_emergence"]
        energy_factor = min(1.0, result["final_energy_avg"] / 100.0)
        
        # Penalize if the blockchain verification failed (unlikely but critical)
        penalty = 1.0 if result["provenance_valid"] else 0.1
        
        fitness = (0.7 * emergence + 0.3 * energy_factor) * penalty
        candidate["fitness"] = fitness
        return fitness

    def mutate(self, parent: Dict[str, Any]) -> Dict[str, Any]:
        """Mutates parent parameter values slightly."""
        child = parent.copy()
        
        # Mutate sharing parameters
        child["sharing_rate"] = max(0.05, min(0.50, round(parent["sharing_rate"] + random.uniform(-0.06, 0.06), 3)))
        child["safety_threshold"] = max(10.0, min(40.0, round(parent["safety_threshold"] + random.uniform(-3.0, 3.0), 1)))
        
        # Mutate policy weights
        child["cooperation_weight"] = max(0.0, min(1.0, round(parent["cooperation_weight"] + random.uniform(-0.15, 0.15), 3)))
        child["consensus_weight"] = max(0.0, min(1.0, round(parent["consensus_weight"] + random.uniform(-0.15, 0.15), 3)))
        
        child["fitness"] = 0.0
        return child

    def run_evolution(self, generations: int = 3, population_size: int = 4, steps_per_trial: int = 15) -> Dict[str, Any]:
        """Runs the continuous benchmarking evolutionary optimization loop.
        
        Logs the best parameters found in each generation.
        """
        print(f"Starting evolutionary prompt/parameter tuning...")
        
        # Initialize population
        population = [self.create_random_candidate() for _ in range(population_size)]
        
        best_overall = None

        for gen in range(1, generations + 1):
            print(f"\n--- Generation {gen:02d} ---")
            
            # Evaluate all
            for idx, candidate in enumerate(population):
                self.evaluate_candidate(candidate, steps=steps_per_trial)
                print(
                    f"  Candidate {idx+1:02d} | Fitness: {candidate['fitness']:.4f} | "
                    f"Rate: {candidate['sharing_rate']:.3f} | Safety: {candidate['safety_threshold']:.1f} | "
                    f"Coop: {candidate['cooperation_weight']:.2f} | Consen: {candidate['consensus_weight']:.2f}"
                )
                
            # Sort by fitness (descending)
            population.sort(key=lambda c: c["fitness"], reverse=True)
            
            best_gen = population[0]
            print(f"  Best in Gen {gen:02d}: Fitness = {best_gen['fitness']:.4f}")
            
            if best_overall is None or best_gen["fitness"] > best_overall["fitness"]:
                best_overall = best_gen.copy()

            # Breed next generation (Elitism + Mutation)
            next_pop = [best_gen] # Keep best (elitism)
            
            # Mutate survivors to fill population
            while len(next_pop) < population_size:
                parent = random.choice(population[:2]) # select from top 2
                next_pop.append(self.mutate(parent))
                
            population = next_pop

        print("\n" + "=" * 60)
        print(" EVOLUTIONARY PARAMETER TUNING SUMMARY")
        print("=" * 60)
        print(f"Optimized sharing_rate:    {best_overall['sharing_rate']:.3f}") # type: ignore
        print(f"Optimized safety_threshold: {best_overall['safety_threshold']:.1f}") # type: ignore
        print(f"Optimized coop_weight:      {best_overall['cooperation_weight']:.2f}") # type: ignore
        print(f"Optimized consen_weight:    {best_overall['consensus_weight']:.2f}") # type: ignore
        print(f"Maximized Fitness Score:    {best_overall['fitness']:.4f}") # type: ignore
        print("=" * 60)
        
        return best_overall # type: ignore
