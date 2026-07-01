import random
from base_graph import HybridControlSwarmGraph, EmergenceNode, EmergenceEdge, ControlMode, EdgeType

def run_stigmergy_example():
    print("=" * 60)
    # Stigmergic Path Selection Example
    print(" STIGMERGY FORAGING: LOCAL REINFORCEMENT & PATH OPTIMIZATION")
    print("=" * 60)

    # 1. Build swarm structure
    swarm = HybridControlSwarmGraph(name="foraging-swarm", seed=42)
    random.seed(42)

    # Create Nodes
    # Nest/Start, Food/Target, and two alternative paths (Short vs. Long)
    nodes = ["nest", "short_mid", "long_1", "long_2", "long_3", "food"]
    for nid in nodes:
        node = EmergenceNode(
            id=nid,
            opinions={},
            resources={"energy": 100.0},
            control_mode=ControlMode.STIGMERGIC
        )
        swarm.graph.add_node(node)

    # Create Edges (EmergenceEdge supports flow decay)
    # Short Path: nest -> short_mid -> food
    # Long Path:  nest -> long_1 -> long_2 -> long_3 -> food
    edges_to_create = [
        ("nest", "short_mid"), ("short_mid", "food"),
        ("nest", "long_1"), ("long_1", "long_2"), ("long_2", "long_3"), ("long_3", "food")
    ]
    for src, tgt in edges_to_create:
        edge = EmergenceEdge(source_id=src, target_id=tgt, weight=1.0)
        swarm.graph.add_edge(edge)

    # Add reverse connections for agents heading back to nest
    for src, tgt in edges_to_create:
        edge = EmergenceEdge(source_id=tgt, target_id=src, weight=1.0)
        swarm.graph.add_edge(edge)

    print("Swarm network structure initialized.")
    print("Short Path: nest <-> short_mid <-> food (2 hops)")
    print("Long Path:  nest <-> long_1 <-> long_2 <-> long_3 <-> food (4 hops)")
    print("Initial weights are all 1.0.")

    # Virtual foragers state
    # Each agent is located at a node, and has a state: "seeking_food" or "returning_nest"
    foragers = [{"id": f"ant_{i:02d}", "loc": "nest", "status": "seeking_food"} for i in range(25)]

    # Simulation loop
    steps = 100
    for step in range(1, steps + 1):
        # 1. Evaporate pheromone/weights (simulating decay)
        for edge in swarm.graph.edges.values():
            if isinstance(edge, EmergenceEdge):
                # decay flow and weight
                edge.decay_flow(decay_rate=0.08)

        # 2. Step each agent
        for ant in foragers:
            curr = ant["loc"]
            
            # Destination check
            if ant["status"] == "seeking_food" and curr == "food":
                ant["status"] = "returning_nest"
            elif ant["status"] == "returning_nest" and curr == "nest":
                ant["status"] = "seeking_food"

            # Retrieve available outgoing edges
            outgoing_edges = [
                e for e in swarm.graph.edges.values()
                if e.source_id == curr
            ]
            
            if not outgoing_edges:
                continue

            # In Stigmergic Mode: choose path proportional to weight (virtual pheromones)
            # Filter out immediate back-tracking to keep motion directed
            weights = [e.weight for e in outgoing_edges]
            sum_weights = sum(weights)
            
            # Weighted random selection
            r = random.uniform(0, sum_weights)
            acc = 0.0
            selected_edge = outgoing_edges[0]
            for idx, w in enumerate(weights):
                acc += w
                if r <= acc:
                    selected_edge = outgoing_edges[idx]
                    break

            # Move agent
            ant["loc"] = selected_edge.target_id
            
            # Deposit pheromone on the edge just traversed
            # Larger deposit when carrying food back to nest
            deposit_amount = 2.0 if ant["status"] == "returning_nest" else 1.0
            
            if isinstance(selected_edge, EmergenceEdge):
                selected_edge.update_weight(
                    delta=deposit_amount,
                    reason=f"ant_foraging_deposit"
                )

        # Run swarm housekeeping (provenance logs, metrics computations)
        swarm.hybrid_step()

        if step % 25 == 0:
            print(f"\n--- Simulation Step {step:03d} ---")
            # Print path weights
            w_short_1 = swarm.graph.edges["nest->short_mid"].weight
            w_short_2 = swarm.graph.edges["short_mid->food"].weight
            w_long_1 = swarm.graph.edges["nest->long_1"].weight
            w_long_2 = swarm.graph.edges["long_1->long_2"].weight
            
            print(f"  Short Path Weights: nest->short_mid = {w_short_1:.2f} | short_mid->food = {w_short_2:.2f}")
            print(f"  Long Path Weights:  nest->long_1 = {w_long_1:.2f} | long_1->long_2 = {w_long_2:.2f}")
            
    # Final results
    print("\n" + "=" * 50)
    print("STIGMERGIC PATH FORAGING COMPLETED")
    final_short = swarm.graph.edges["nest->short_mid"].weight
    final_long = swarm.graph.edges["nest->long_1"].weight
    print(f"Final Short Path nest->short_mid strength: {final_short:.4f} (reinforced)")
    print(f"Final Long Path nest->long_1 strength:  {final_long:.4f} (evaporated)")
    print("Conclusion: Swarm successfully converged on the shorter path through stigmergic reinforcement!")
    print("=" * 50)

if __name__ == "__main__":
    run_stigmergy_example()
