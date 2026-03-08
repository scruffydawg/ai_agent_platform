from src.core.orchestrator import Orchestrator
from src.agents.base import BaseAgent
from src.core.state import state_manager

# Mock LLM Client that doesn't actually hit the API for tests
class MockLLM:
    def __init__(self, *args, **kwargs):
        pass
    def generate(self, messages, timeout=30):
        # Fake logic for routing
        content = messages[-1]['content'].lower()
        if "research" in content:
             return "I must route this to the researcher agent."
        return "I can handle this myself."

def test_orchestration():
    print("--- Testing Orchestrator ---")
    
    # 1. Setup Agents
    orchestrator = Orchestrator()
    orchestrator.llm = MockLLM() # override with mock
    
    researcher = BaseAgent(agent_id="researcher", system_prompt="You do research.")
    researcher.llm = MockLLM()
    
    orchestrator.register_agent(researcher)
    
    # 2. Test routing to self
    res1 = orchestrator.run("Hello, how are you?")
    assert "status" in res1
    print(f"Self-Routing Result: {res1['status']}")
    
    # 3. Test routing to sub-agent
    res2 = orchestrator.run("Please research the history of AI.")
    # In our mock routing, this string should trigger the 'researcher' block
    assert "status" in res2
    print(f"Delegated Routing Result: {res2['status']}")

    # 4. Test Kill Switch in Agent Loop
    print("\n--- Testing Agent Kill Switch ---")
    state_manager.trigger_halt("User pressed Ctrl+C")
    res3 = orchestrator.run("Do something else.")
    assert int(res3.get("status") == "halted")
    print(f"Kill Switch Result: {res3['status']}")

if __name__ == "__main__":
    test_memory = test_orchestration()
