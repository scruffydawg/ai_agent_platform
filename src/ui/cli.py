import sys
from typing import Any
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm
from src.core.state import state_manager

class CLI:
    """
    User Interface designed for low cognitive load and clear state signaling.
    """
    def __init__(self):
        self.console = Console()

    def print_state(self, agent_name: str, state: str, details: str = ""):
        """
        Prints the current state of an agent (e.g., Thinking, Acting).
        Colors: 
        - Cyan: Thinking/Reasoning
        - Green: Success/Completed
        - Yellow: Acting/Tools
        - Red: Error/Halted
        """
        color = "white"
        if state.lower() == "thinking": color = "cyan"
        elif state.lower() == "acting": color = "yellow"
        elif state.lower() == "success": color = "green"
        elif state.lower() in ["error", "halted"]: color = "red"

        msg = f"[{color} bold]{agent_name}[/] | [{color}]{state}[/]"
        if details:
            msg += f"\n[dim]{details}[/]"
            
        self.console.print(Panel(msg, border_style=color, expand=False))

    def require_confirmation(self, action_summary: str) -> bool:
        """
        Interrupts flow to ask the user to confirm a risky action.
        This aligns with the 'Triggered Processes Only' logic for file IO/Terminal.
        """
        if state_manager.is_halted():
             self.console.print("[bold red]System is currently halted. Cannot proceed with action.[/]")
             return False
             
        self.console.print(f"\n[bold yellow]Agent intends to perform the following action:[/]")
        self.console.print(Panel(f"[white]{action_summary}[/]", border_style="yellow", expand=False))
        
        # We use standard input to allow easy override, default is 'No' for safety
        is_confirmed = Confirm.ask("Do you want to allow this action?", default=False)
        
        if not is_confirmed:
             self.console.print("[bold red]Action denied by user.[/]")
        else:
             self.console.print("[bold green]Action approved.[/]")
             
        return is_confirmed

    def print_error(self, message: str):
        self.console.print(f"[bold red]ERROR:[/] {message}")
        
    def print_success(self, message: str):
         self.console.print(f"[bold green]SUCCESS:[/] {message}")

    def start_progress(self, message: str):
        """Starts a persistent progress indicator for graph execution (Neon Dark Theme)."""
        from rich.progress import Progress, SpinnerColumn, TextColumn
        self.progress = Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=self.console,
            transient=True
        )
        self.progress.start()
        self.progress_task = self.progress.add_task(description=message, total=None)

    def update_progress(self, message: str):
        """Updates the description of the current progress task."""
        if hasattr(self, 'progress') and hasattr(self, 'progress_task'):
            self.progress.update(self.progress_task, description=f"[cyan]{message}[/]")

    def stop_progress(self, success: bool = True, msg: str = ""):
        """Stops the progress indicator and prints a final result."""
        if hasattr(self, 'progress'):
            self.progress.stop()
            if msg:
                if success:
                    self.print_success(msg)
                else:
                    self.print_error(msg)
            del self.progress
            del self.progress_task

    def print_tool_output(self, tool_name: str, data: Any):
        """
        Renders tool outputs in a distinct visual block (Phase 1 Refactor).
        Separates 'Agent Thoughts' from 'Raw Data'.
        """
        from rich.syntax import Syntax
        import json

        content = data
        if not isinstance(data, str):
            try:
                content = json.dumps(data, indent=2)
            except:
                content = str(data)

        syntax = Syntax(content, "json" if "{" in str(content) else "text", theme="monokai", line_numbers=True)
        self.console.print(Panel(syntax, title=f"[yellow]Tool Result: {tool_name}[/]", border_style="yellow"))

# Singleton instance
cli = CLI()
