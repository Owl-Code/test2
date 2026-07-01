import random
from base_graph import HybridControlSwarmGraph, EmergenceNode, ControlMode, AdaptiveEdge

def run_diffusion_comparison():
    print("=" * 60)
    print(" OPINION DYNAMICS: POLARIZATION vs CONSENSUS COMPARISON")
    print("=" * 60)

    # Helper to build a ring-like lattice with shortcuts (Watts-Strogatz variant)
    def build_test_swarm(name: str, seed: int) -> HybridControlSwarmGraph:
        swarm = HybridControlSwarmGraph(name=name, seed=seed)
        random.seed(seed)
        n_nodes = 20
        
        # 1. Create nodes with random opinions evenly distributed between -1.0 and 1.0
        for i in range(n_nodes):
            node_id = f"agent_{i:02d}"
            # Alternating polar opinions to start
            op_val = -0.8 if i % 2 == 0 else 0.8
            node = EmergenceNode(
                id=node_id,
                opinions={"opinion_topic": op_val},
                control_mode=ControlMode.DECENTRALIZED
            )
            swarm.graph.add_node(node)
            
        # 2. Wire in a cycle structure
        for i in range(n_nodes):
            src = f"agent_{i:02d}"
            tgt = f"agent_{(i + 1) % n_nodes:02d}"
            swarm.graph.add_edge(AdaptiveEdge(source_id=src, target_id=tgt))
            
        # 3. Add random shortcuts
        for _ in range(10):
            s = f"agent_{random.randint(0, n_nodes - 1):02d}"
            t = f"agent_{random.randint(0, n_nodes - 1):02d}"
            if s != t:
                swarm.graph.add_edge(AdaptiveEdge(source_id=s, target_id=t))
                
        return swarm

    # Run Swarm A: Low Epsilon (Polarization Expected)
    print("\n[Case A] Running with Epsilon = 0.3 (Strict boundaries; high polarization expected)...")
    swarm_a = build_test_swarm("polar-swarm", 101)
    # Run diffusion subgraph opinion model
    traj_a = swarm_a.diffusion_subgraph.run_diffusion(
        model="opinion",
        steps=50,
        params={"epsilon": 0.3, "topic": "opinion_topic"}
    )
    
    opinions_a = [v["opinion_topic"] for v in traj_a.final_state.values()]
    print(f"Completed in {traj_a.steps_run} steps.")
    print("Final Opinions Distribution:")
    print(f"  Min: {min(opinions_a):+.4f} | Max: {max(opinions_a):+.4f}")
    # Print counts of polarized values
    left = sum(1 for v in opinions_a if v < 0)
    right = sum(1 for v in opinions_a if v >= 0)
    print(f"  Left opinions count (<0): {left} | Right opinions count (>=0): {right}")
    print(f"  Final state consensus entropy: {traj_a.entropy_curve[-1]:.4f} (High entropy = polarized clusters)")

    # Run Swarm B: High Epsilon (Consensus Expected)
    print("\n[Case B] Running with Epsilon = 0.9 (Broad confidence; consensus expected)...")
    swarm_b = build_test_swarm("consensus-swarm", 101)
    traj_b = swarm_b.diffusion_subgraph.run_diffusion(
        model="opinion",
        steps=50,
        params={"epsilon": 0.9, "topic": "opinion_topic"}
    )
    
    opinions_b = [v["opinion_topic"] for v in traj_b.final_state.values()]
    print(f"Completed in {traj_b.steps_run} steps.")
    print("Final Opinions Distribution:")
    print(f"  Min: {min(opinions_b):+.4f} | Max: {max(opinions_b):+.4f}")
    print(f"  Final state consensus entropy: {traj_b.entropy_curve[-1]:.4f} (Low entropy = unified opinion)")

    print("\nComparison summary completed.")

if __name__ == "__main__":
    run_diffusion_comparison()
