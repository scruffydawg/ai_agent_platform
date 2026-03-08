import os
from src.memory.manager import MemoryManager

class MockLLM:
    def generate(self, messages, timeout=30):
        return "This is a summary of the deleted history."

def test_compression():
    print("--- Testing Memory Compression ---")
    m = MemoryManager("test_compress_agent", "You are a test agent.")
    
    # 1. Fill history with 25 messages (above threshold 20)
    for i in range(25):
        m.add_message("user", f"Message {i}")
        
    initial_count = len(m.memory.entries)
    print(f"Initial message count: {initial_count}")
    
    # 2. Trigger Compression
    llm = MockLLM()
    success = m.compress_history(llm, threshold=20)
    
    assert success is True
    final_count = len(m.memory.entries)
    print(f"Final message count: {final_count}")
    
    # Should be: 1 (Summary) + 10 (Last 10) = 11
    assert final_count == 11
    assert "SUMMARY" in m.memory.entries[0].content
    
    print("Compression Test Passed!")
    
    # Cleanup
    m.clear()

if __name__ == "__main__":
    test_compression()
