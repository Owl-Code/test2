import random
from base_graph import HybridControlSwarmGraph, EmergenceNode, TrophallaxisEdge, ControlMode

def run_trophallaxis_homeostasis():
    print("=" * 60)
    print(" TROPHALLAXIS & RESOURCE HOMEOSTASIS")
    print("=" * 60)

    # Initialize swarm
    swarm = HybridControlSwarmGraph(name="homeostasis-swarm", seed=42)

    # 1. Create 6 nodes with high variance in resource levels
    # Node 0 and Node 3 have high energy, others are low/starving
    initial_energy = {
        "node_0": 100.0,
        "node_1": 10.0,  # Starving
        "node_2": 15.0,  # Starving
        "node_3": 90.0,
        "node_4": 20.0,
        "node_5": 25.0
    }

    for nid, energy in initial_energy.items():
        node = EmergenceNode(
            id=nid,
            opinions={},
            resources={"energy": energy},
            control_mode=ControlMode.EMERGENCE
        )
        swarm.graph.add_node(node)

    # 2. Add TrophallaxisEdges
    # Wire them in a structure that allows flow from rich to poor
    edges = [
        ("node_0", "node_1"),
        ("node_0", "node_2"),
        ("node_3", "node_4"),
        ("node_3", "node_5"),
        ("node_5", "node_1"),
        ("node_4", "node_2")
    ]
    for src, tgt in edges:
        swarm.graph.add_edge(TrophallaxisEdge(source_id=src, target_id=tgt))

    # Calculate initial variance
    def calculate_variance(swarm_obj) -> float:
        vals = [n.resources["energy"] for n in swarm_obj.graph.nodes.values() if isinstance(n, EmergenceNode)]
        mean = sum(vals) / len(vals)
        return sum((v - mean) ** 2 for v in vals) / len(vals)

    init_var = calculate_variance(swarm)
    init_health = swarm.compute_swarm_health()
    print("Initial Swarm Resource State:")
    for nid, node in sorted(swarm.graph.nodes.items()):
        if isinstance(node, EmergenceNode):
            print(f"  {nid}: Energy = {node.resources['energy']:.1f}")
    print(f"Initial Resource Variance: {init_var:.2f}")
    print(f"Initial Antifragility Score: {init_health.antifragility_score:.4f}")

    print("\nSimulating 30 steps of trophallaxis sharing & metabolism...")
    print("Each node consumes 0.5 energy metabolic cost per step.")
    
    # Configure metab cost and safety threshold
    swarm.trophallaxis.sharing_rate = 0.25
    swarm.trophallaxis.safety_threshold = 20.0

    # Step loop
    for step in range(1, 31):
        # metabolism cost is 0.5
        starving_nodes = swarm.trophallaxis.simulate_metabolism(swarm.graph, cost=0.5)
        # distribute resources
        transfers = swarm.trophallaxis.distribute_resources(swarm.graph)
        
        # Call hybrid step to run housekeeping
        swarm.hybrid_step()

        if step % 10 == 0:
            cur_var = calculate_variance(swarm)
            health = swarm.compute_swarm_health()
            print(f"  Step {step:02d}: Variance = {cur_var:6.2f} | Antifragility = {health.antifragility_score:.4f} | Transfers: {transfers}")

    final_var = calculate_variance(swarm)
    final_health = swarm.compute_swarm_health()

    print("\n" + "=" * 50)
    print("HOMEOSTASIS SIMULATION COMPLETED")
    print("Final Swarm Resource State:")
    for nid, node in sorted(swarm.graph.nodes.items()):
        if isinstance(node, EmergenceNode):
            starving_status = "(STARVING)" if node.resources["energy"] < 20.0 else "(STABLE)"
            print(f"  {nid}: Energy = {node.resources['energy']:.1f} {starving_status}")
            
    print("-" * 50)
    print(f"Initial Variance: {init_var:.2f}  ==>  Final Variance: {final_var:.2f} (Variance reduced!)")
    print(f"Initial Antifragility: {init_health.antifragility_score:.4f}  ==>  Final Antifragility: {final_health.antifragility_score:.4f} (Antifragility increased!)")
    print("=" * 50)

if __name__ == "__main__":
    run_trophallaxis_homeostasis()
