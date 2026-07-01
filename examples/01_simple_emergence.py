import random
import time
from base_graph import HybridControlSwarmGraph, EmergenceNode, EmergenceEdge, ControlMode, EdgeType
from base_graph.utils import TerminalDashboard

def run_example():
    print("Initializing Emergence Example...")
    # Initialize swarm
    swarm = HybridControlSwarmGraph(name="emergence-swarm", seed=42)
    random.seed(42)

    # 1. Create 30 nodes with random initial opinions and energy levels
    num_nodes = 30
    for i in range(num_nodes):
        node_id = f"node_{i:02d}"
        node = EmergenceNode(
            id=node_id,
            opinions={"main": random.uniform(-1.0, 1.0)},
            resources={"energy": 100.0},
            control_mode=ControlMode.EMERGENCE
        )
        swarm.graph.add_node(node)

    # 2. Add random edges to connect the nodes (average degree 3)
    node_ids = list(swarm.graph.nodes.keys())
    for i in range(num_nodes):
        # Ensure at least 2 edges per node for connectivity
        targets = random.sample(node_ids, 3)
        for t in targets:
            if t != node_ids[i]:
                # Using EmergenceEdge to support flow dynamics
                edge = EmergenceEdge(
                    source_id=node_ids[i],
                    target_id=t,
                    weight=random.uniform(0.5, 1.5)
                )
                swarm.graph.add_edge(edge)

    # Calculate initial stats
    initial_report = swarm.compute_swarm_health()
    print(f"Initial Emergence Level: {initial_report.emergence_level:.4f}")
    print(TerminalDashboard.render(swarm))
    print("\nSimulating 150 steps of local updates...\n")

    # 3. Simulate steps
    for step in range(1, 151):
        # Custom local step logic that drives opinion alignment
        # Nodes will update their opinions towards their neighbors' average opinion
        for node in swarm.graph.nodes.values():
            if isinstance(node, EmergenceNode):
                neighbors = swarm.graph.get_neighbors(str(node.id))
                if neighbors:
                    avg_neigh_op = sum(n.opinions.get("main", 0.0) for n in neighbors) / len(neighbors)
                    # Slowly shift local opinion towards neighbors
                    curr_op = node.opinions.get("main", 0.0)
                    node.opinions["main"] = curr_op + 0.1 * (avg_neigh_op - curr_op)
                    
        # Step the swarm (runs metabolism, trophallaxis, logs provenance)
        swarm.hybrid_step()

        # Render dashboard at key milestones
        if step in [50, 100, 150]:
            print(f"\n--- Milestones: Step {step} ---")
            print(TerminalDashboard.render(swarm))

    final_report = swarm.compute_swarm_health()
    print("\n" + "=" * 50)
    print("SIMULATION COMPLETED SUCCESSFULLY")
    print(f"Initial Emergence Level: {initial_report.emergence_level:.4f}")
    print(f"Final Emergence Level:   {final_report.emergence_level:.4f}")
    print(f"Net Emergence delta:     {final_report.emergence_level - initial_report.emergence_level:+.4f}")
    print("=" * 50)

if __name__ == "__main__":
    run_example()
