import sys
import os

# Insert workspace src/ folder to Python path for direct running
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))

from base_graph import MetaSkillEvolver

def run_benchmarking():
    print("=" * 70)
    print(" CONTINUOUS BENCHMARKING: META-SKILL SWARM PARAMETER EVOLVER")
    print("=" * 70)
    
    # 1. Instantiate the evolver
    evolver = MetaSkillEvolver()
    
    # 2. Run 3 generations of parameter tuning
    best_candidate = evolver.run_evolution(
        generations=3,
        population_size=3,
        steps_per_trial=10
    )
    
    print("\nBenchmark optimization completed successfully.")

if __name__ == "__main__":
    run_benchmarking()
