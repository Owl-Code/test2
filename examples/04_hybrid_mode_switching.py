import time
from base_graph import HybridControlSwarmGraph, EmergenceNode, AdaptiveEdge, ControlMode, EdgeType, Action, Decision

def run_hybrid_mode_switching():
    print("=" * 60)
    print(" HYBRID MODE SWITCHING & COMMAND HANDOFF")
    print("=" * 60)

    # Initialize swarm
    swarm = HybridControlSwarmGraph(name="mode-switching-swarm", seed=42)

    # 1. Create 5 nodes
    num_nodes = 5
    for i in range(num_nodes):
        node_id = f"node_{i}"
        node = EmergenceNode(
            id=node_id,
            opinions={"target": 0.0},
            resources={"energy": 80.0},
            control_mode=ControlMode.DECENTRALIZED
        )
        swarm.graph.add_node(node)

    # Wire nodes in a line: node_0 -> node_1 -> node_2 -> node_3 -> node_4
    for i in range(num_nodes - 1):
        swarm.graph.add_edge(AdaptiveEdge(
            source_id=f"node_{i}",
            target_id=f"node_{i+1}",
            edge_type=EdgeType.COMMUNICATION
        ))

    print(f"Swarm initialized in: {ControlMode.DECENTRALIZED.value} mode.")
    print("Simulating 5 initial steps of opinion convergence...")
    for _ in range(5):
        swarm.hybrid_step()

    # 2. Inject Hierarchical Command
    print("\n--- PHASE 2: INJECTING HIERARCHICAL COMMAND ---")
    print("Promoting 'node_0' to leader and switching followers to HIERARCHICAL.")
    
    # Establish command edges
    for i in range(1, num_nodes):
        cmd_edge = AdaptiveEdge(
            source_id="node_0",
            target_id=f"node_{i}",
            edge_type=EdgeType.COMMAND,
            weight=2.0
        )
        # Inject command into metadata
        cmd_edge.metadata["command_type"] = "BOOST_ENERGY"
        cmd_edge.metadata["command_params"] = {"amount": 15.0}
        swarm.graph.add_edge(cmd_edge)

    # Policy function that executes commands on boost energy
    def custom_boost_policy(node: EmergenceNode, action_space: list, context: dict) -> Decision:
        commands = context.get("incoming_commands", [])
        if commands:
            cmd = commands[0]
            if cmd["type"] == "BOOST_ENERGY":
                amt = cmd["params"].get("amount", 5.0)
                # Boost node energy
                node.resources["energy"] += amt
                return Decision(
                    node_id=str(node.id),
                    selected_action=Action(
                        action_type="SHARE_RESOURCE",
                        parameters={"boosted": True, "amount": amt}
                    ),
                    confidence=1.0,
                    reason="Executing hierarchical boost energy command"
                )
        return Decision(
            node_id=str(node.id),
            selected_action=Action(action_type="IDLE", parameters={}),
            confidence=0.5,
            reason="No command matching BOOST_ENERGY found"
        )

    # Switch followers and leader control modes
    mode_updates = {f"node_{i}": ControlMode.HIERARCHICAL for i in range(num_nodes)}
    swarm.set_control_mode(mode_updates)
    
    # Setup policy to execute command boost
    for node in swarm.graph.nodes.values():
        if isinstance(node, EmergenceNode) and node.id != "node_0":
            node.policy = custom_boost_policy

    # Execute 3 steps in hierarchical mode
    print("Running 3 steps in HIERARCHICAL mode...")
    for step in range(3):
        res = swarm.hybrid_step()
        print(f"  Step {swarm.step_index} - node_1 energy: {swarm.graph.nodes['node_1'].resources['energy']:.1f}")

    # 3. Release back to Stigmergic mode
    print("\n--- PHASE 3: RELEASING TO STIGMERGIC MODE ---")
    swarm.set_control_mode(ControlMode.STIGMERGIC)
    
    # Clear custom policies
    for node in swarm.graph.nodes.values():
        if isinstance(node, EmergenceNode):
            node.policy = None

    print("Running 4 steps in STIGMERGIC mode...")
    for _ in range(4):
        swarm.hybrid_step()

    # 4. Print Provenance Log Trail
    print("\n" + "=" * 50)
    print("PROVENANCE VERIFICATION LOGS")
    print("=" * 50)
    print(f"Cryptographic Chain Integrity Check: {'VALID' if swarm.provenance.verify_chain() else 'FAIL'}")
    print(f"Total transactions logged: {len(swarm.provenance.chain)}")
    print("\nRecent Ledger Modifications:")
    for record in swarm.provenance.chain[-8:]:
        delta = record.delta
        print(f"  [{record.index:02d}] {delta.actor} -> {delta.operation} (Target: {delta.target}) | Hash: {record.current_hash[:12]}...")
    print("=" * 50)

if __name__ == "__main__":
    run_hybrid_mode_switching()
