import time
from typing import Optional, Dict, Any
import traceback
from src.core.state import state_manager, recovery_manager
from src.llm.client import LLMClient
from src.memory.manager import MemoryManager

class BaseAgent:
    """
    Abstract Base Agent enforcing the Observe -> Reason -> Act loop.
    Strictly checks the KILL SWITCH (state_manager) at every step.
    """
    def __init__(self, agent_id: str, system_prompt: str, model: str = "gpt-3.5-turbo"):
        self.agent_id = agent_id
        self.session_id = agent_id
        self.system_prompt = system_prompt
        self.memory = MemoryManager(agent_id=agent_id, system_prompt=system_prompt)
        self.llm = LLMClient(model=model)
        self.max_loops = 5 # Safety limit to prevent dead loops
        
    async def observe(self, incoming_data: str) -> str:
        """Parses incoming data or sensory input."""
        return f"Observation: {incoming_data}"

    async def reason(self, observation: str) -> Optional[str]:
        """Calls the LLM to decide the next action based on context."""
        if state_manager.is_halted():
             return None
             
        # Initialize memory if not already done
        if self.memory.memory is None:
            await self.memory.initialize()

        await self.memory.add_message("user", observation)
        
        # Inject learned patterns into the context
        learnings = self.memory.get_learning_summary()
        prompt_with_learnings = self.system_prompt
        if learnings:
            prompt_with_learnings += f"\n\n## ADAPTIVE LEARNINGS\n{learnings}"
            
        messages = [{"role": "system", "content": prompt_with_learnings}]
        messages.extend(self.memory.get_messages(limit=10)[1:]) # Avoid double system prompt
        
        # Timeout and kill switch are enforced inside the LLMClient layer
        response = await self.llm.generate_async(messages)
        
        if response:
             await self.memory.add_message("assistant", response)
             
        return response

    async def act(self, plan: str) -> Dict[str, Any]:
        """Executes the plan. (To be overridden by subclasses with specific skills)"""
        # In base agent, we just return the plan as the action.
        return {"status": "success", "action": "raw_response", "data": plan}

    async def run(self, initial_input: str) -> Dict[str, Any]:
        """Executes the core agent loop with strict limits."""
        loop_count = 0
        current_input = initial_input
        final_result = None

        # Ensure memory is initialized
        if self.memory.memory is None:
            await self.memory.initialize()

        while loop_count < self.max_loops:
            if state_manager.is_halted():
                print(f"[{self.agent_id}] HALTED before loop {loop_count}.")
                return {"status": "halted"}

            print(f"[{self.agent_id}] Loop {loop_count} starting...")
            
            # Step 1: Observe
            observation = await self.observe(current_input)
            
            # Step 2: Reason
            plan = await self.reason(observation)
            
            if not plan: # usually happens if LLM fails or system halts
                return {"status": "error", "message": "Failed to generate plan."}

            if state_manager.is_halted(): return {"status": "halted"}
                
            # Step 3: Act
            try:
                result = await self.act(plan)
                recovery_manager.clear_errors(self.session_id)
                
                # Phase 13: Extract learning insight from successful action
                if result.get("status") == "success":
                    insight_prompt = f"Based on the following action and result, what is a single concise fact learned about the user's preference or the environment? (Format: One sentence starting with 'The user...' or 'The system...')\n\nAction: {plan}\nResult: {result}"
                    insight = await self.llm.generate_async([{"role": "system", "content": "You are a learning observer."}, {"role": "user", "content": insight_prompt}])
                    if insight:
                        if "user" in insight.lower():
                            await self.memory.record_user_learn(insight, context=f"Action: {plan}")
                        else:
                            await self.memory.record_self_learn(insight, context=f"Action: {plan}")
            except Exception as e:
                error_trace = traceback.format_exc()
                print(f"[{self.agent_id}] Tool exception caught: {e}")
                
                if recovery_manager.register_error(self.session_id, str(e)):
                    print(f"[{self.agent_id}] CIRCUIT BROKEN (Max retries reached).")
                    return {"status": "blocked", "message": f"Circuit Broken! Escalating to human.\nError: {str(e)}", "traceback": error_trace}
                
                ouch_message = f"[SYSTEM ERROR] Your previous action failed with:\n{error_trace}\nPlease analyze this failure and try an alternative approach."
                await self.memory.add_message("system", ouch_message)
                
                current_input = ouch_message
                loop_count += 1
                continue
            
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

        return final_result or {"status": "error", "message": "Execution loop exhausted without success"}
