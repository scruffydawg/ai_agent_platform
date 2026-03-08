from src.ui.cli import cli
from src.utils.logger import logger
from src.core.state import state_manager

def test_ui_and_logs():
    print("--- Testing UI and Logger ---")
    
    # Send events to logger
    logger.debug("This is a unseen debug message")
    logger.info("This is an info message")
    logger.error("This is an error message")
    print("Logs written. Check data/logs/system.log")

    # Display states
    cli.print_state("Orchestrator", "Thinking", "Analyzing the user prompt for keywords.")
    cli.print_state("Researcher", "Acting", "Using tool: WebSearch")
    cli.print_state("Coder", "Success", "File written to data/output.py")
    
    # Test confirmation (Simulated bypass since we can't easily script standard input confirmation in this pipeline)
    print("\n[Simulated] Skipping UI 'Confirm' block since it requires manual keyboard input.")
    
    # Test Halt UI state
    state_manager.trigger_halt("Test Kill Switch triggered via StateManager.")
    
    if state_manager.is_halted():
         cli.print_state("System", "Halted", "Kill switch is active!")
         
if __name__ == "__main__":
    test_ui_and_logs()
