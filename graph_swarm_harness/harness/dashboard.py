from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.columns import Columns
from rich.text import Text
from rich import box

from graph_swarm_harness.core.graph_state import SwarmGraphState
from graph_swarm_harness.core.emergence import calculate_swarm_emergence

class SwarmTerminalDashboard:
    """Uses Rich to build a beautiful terminal representation of the swarm status."""
    
    def __init__(self):
        self.console = Console()

    def render(self, swarm: SwarmGraphState, last_decision_summary: str = ""):
        """Prints the current swarm status dashboard directly to the terminal."""
        import sys
        if sys.stdout.isatty():
            self.console.clear()
        
        # 1. Swarm Info Panel
        agents = swarm.get_agents()
        emergence = calculate_swarm_emergence(swarm)
        
        header_text = Text()
        header_text.append(f"* Graph Swarm: {swarm.name.upper()}  ", style="bold cyan")
        header_text.append(f"|  Tick: #{swarm.step_index}  ", style="bold yellow")
        header_text.append(f"|  Active Goals: {swarm.active_goals}\n", style="bold white")
        
        # Check provenance chain validity
        prov_valid = swarm.provenance.verify_chain()
        prov_status = "[bold green]SECURE[/bold green]" if prov_valid else "[bold red]COMPROMISED[/bold red]"
        
        metrics_text = Text.from_markup(
            f"* [bold]Swarm Emergence:[/bold] {emergence:.4f}  "
            f"|  [bold]Nodes/Edges:[/bold] {len(swarm.graph.nodes)}/{len(swarm.graph.edges)}  "
            f"|  [bold]Provenance Audit:[/bold] {prov_status}  "
            f"|  [bold]Dominant Mode:[/bold] {agents[0].node.control_mode.value if agents else 'NONE'}"
        )
        
        self.console.print(Panel(
            Text.assemble(header_text, "\n", metrics_text),
            title="[bold green]Orchestration Engine Summary[/bold green]",
            border_style="green",
            box=box.DOUBLE
        ))

        # 2. Agent Information Table
        agent_table = Table(title="[bold cyan]Active Dynamic Agent Status[/bold cyan]", box=box.ROUNDED, border_style="cyan")
        agent_table.add_column("Agent ID", style="bold yellow")
        agent_table.add_column("Role", style="green")
        agent_table.add_column("Energy", justify="right")
        agent_table.add_column("Opinion (Main)", justify="right")
        agent_table.add_column("Emergence Contrib", justify="right")
        agent_table.add_column("Skills", style="magenta")
        agent_table.add_column("Last Thought / Rationale", style="italic white")
        
        for agent in agents:
            # Color code energy
            energy = agent.energy
            energy_style = "bold red" if energy < 20.0 else "bold yellow" if energy < 50.0 else "bold green"
            
            # Retrieve last thought or idle
            last_thought = agent.node.local_memory.get("last_decision_reason", "Idling...")
            if len(last_thought) > 40:
                last_thought = last_thought[:37] + "..."
                
            opinion_val = agent.node.opinions.get("main", 0.0)
            
            agent_table.add_row(
                agent.id,
                agent.role.upper(),
                Text(f"{energy:.1f}%", style=energy_style),
                f"{opinion_val:+.2f}",
                f"{agent.emergence_level:.2f}",
                ", ".join(agent.active_skills),
                last_thought
            )
            
        self.console.print(agent_table)

        # 3. Last Action Console logs
        if last_decision_summary:
            self.console.print(Panel(
                last_decision_summary, 
                title="[bold yellow]Last Step Execution Logs[/bold yellow]", 
                border_style="yellow"
            ))

        # 4. Provenance chain tail logs
        provenance_table = Table(title="[bold magenta]Recent Provenance Mutated Events (Audit Trail)[/bold magenta]", box=box.SIMPLE, border_style="magenta")
        provenance_table.add_column("Index", style="dim")
        provenance_table.add_column("Actor")
        provenance_table.add_column("Operation")
        provenance_table.add_column("Target")
        provenance_table.add_column("Current State SHA Hash", style="dim cyan")
        
        for record in swarm.provenance.chain[-5:]:
            provenance_table.add_row(
                str(record.index),
                record.delta.actor,
                record.delta.operation,
                record.delta.target,
                record.current_hash[:16] + "..."
            )
        self.console.print(provenance_table)
        self.console.print("\n")
