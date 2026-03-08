import time
from typing import Optional, Dict, Any
from src.core.state import state_manager
from src.llm.client import LLMClient
from src.memory.manager import MemoryManager

class BaseAgent:
    """
    Abstract Base Agent enforcing the Observe -> Reason -> Act loop.
    Strictly checks the KILL SWITCH (state_manager) at every step.
    """
    def __init__(self, agent_id: str, system_prompt: str, model: str = "gpt-3.5-turbo"):
        self.agent_id = agent_id
        self.system_prompt = system_prompt
        self.memory = MemoryManager(agent_id=agent_id, system_prompt=system_prompt)
        self.llm = LLMClient(model=model)
        self.max_loops = 5 # Safety limit to prevent dead loops
        
    def observe(self, incoming_data: str) -> str:
        """Parses incoming data or sensory input."""
        return f"Observation: {incoming_data}"

    def reason(self, observation: str) -> Optional[str]:
        """Calls the LLM to decide the next action based on context."""
        if state_manager.is_halted():
             return None
             
        self.memory.add_message("user", observation)
        messages = self.memory.get_messages()
        
        # Timeout and kill switch are enforced inside the LLMClient layer
        response = self.llm.generate(messages)
        
        if response:
             self.memory.add_message("assistant", response)
             
        return response

    def act(self, plan: str) -> Dict[str, Any]:
        """Executes the plan. (To be overridden by subclasses with specific skills)"""
        # In base agent, we just return the plan as the action.
        return {"status": "success", "action": "raw_response", "data": plan}

    def run(self, initial_input: str) -> Dict[str, Any]:
        """Executes the core agent loop with strict limits."""
        loop_count = 0
        current_input = initial_input
        final_result = None

        while loop_count < self.max_loops:
            if state_manager.is_halted():
                print(f"[{self.agent_id}] HALTED before loop {loop_count}.")
                return {"status": "halted"}

            print(f"[{self.agent_id}] Loop {loop_count} starting...")
            
            # Step 1: Observe
            observation = self.observe(current_input)
            
            # Step 2: Reason
            plan = self.reason(observation)
            
            if not plan: # usually happens if LLM fails or system halts
                return {"status": "error", "message": "Failed to generate plan."}

            if state_manager.is_halted(): return {"status": "halted"}

            # Step 3: Act
            result = self.act(plan)
            
            # Simple break condition: if action was just to respond, we stop.
            # Complex agents might loop here if they need to fetch more data.
            if result.get("status") == "success":
                final_result = result
                break

            loop_count += 1
            current_input = f"Action Result: {result}" # Feed result back into next loop

        if loop_count >= self.max_loops:
             print(f"[{self.agent_id}] Max loops ({self.max_loops}) reached. Forcing exit.")
             return {"status": "max_loops_reached", "last_result": final_result}

        return final_result
