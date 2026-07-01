import os
import sys
import asyncio

# Ensure current directory is in python path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from graph_swarm_harness.harness.main_loop import SwarmHarnessOrchestrator

async def main_async():
    print("=== Launching Graph Swarm Harness Integration Trial ===")
    
    # 1. Initialize Orchestrator pointing to config
    config_path = os.path.join("graph_swarm_harness", "config.yaml")
    orchestrator = SwarmHarnessOrchestrator(config_path=config_path)
    
    # Force auto confirm to True for automated testing
    orchestrator.agent_executor.auto_confirm = True
    
    # 2. Boot Swarm (bootstrap fresh coordinator)
    swarm = orchestrator.setup_swarm(resume=False)
    print(f"Initial Swarm Setup Complete: {swarm.name}")
    print(f"Dominant Goals: {swarm.active_goals}")
    
    # 3. Spawn a child agent dynamically from coordinator context (pre-loop)
    # The coordinator will spawn its sub-agents, but we spawn a 'coder' to bootstrap interaction.
    print("Spawning worker 'coder' agent...")
    coder_id = swarm.spawn_dynamic_agent(
        role="coder",
        initial_skills=["code_execution", "file_io"],
        initial_tools=["write_file", "execute_python_snippet", "create_handoff_edge"],
        parent_id=swarm.get_agents()[0].id
    )
    
    # Spawning a 'reviewer' agent
    print("Spawning reviewer agent...")
    reviewer_id = swarm.spawn_dynamic_agent(
        role="reviewer",
        initial_skills=["file_io", "self_reflect_and_emergence_update"],
        initial_tools=["read_file", "create_handoff_edge"],
        parent_id=swarm.get_agents()[0].id
    )
    
    # Send a bootstrapping message to the coder inbox
    swarm.get_agent(coder_id).receive_message(
        sender_id=swarm.get_agents()[0].id,
        message="Please write a python snippet that calculates the factorial of 5 and execute it."
    )
    
    # 4. Execute 3 ticks in the loop
    ticks = 3
    print(f"\nStarting Harness Event Loop ({ticks} ticks, auto-confirm=True)...")
    for tick in range(1, ticks + 1):
        print(f"\n--- EXECUTION TICK #{tick} ---")
        log_summary = await orchestrator.run_tick()
        print(log_summary)
        
    print("\n=== Integration Trial Finished Successfully ===")

def main():
    asyncio.run(main_async())

if __name__ == "__main__":
    main()
