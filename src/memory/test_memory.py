from src.memory.manager import MemoryManager

def test_memory():
    m = MemoryManager("test_agent", "You are a test agent.")
    m.add_message("user", "Hello!")
    m.add_message("assistant", "Hi there!")
    
    msgs = m.get_messages()
    assert len(msgs) == 3 # System, user, assistant
    print(f"Messages: {msgs}")
    
    # Test persistence by reloading
    m2 = MemoryManager("test_agent", "You are a test agent.")
    msgs2 = m2.get_messages()
    assert len(msgs) == len(msgs2)
    print("Persistence works!")
    
    # Cleanup
    m2.clear()
    print("Cleanup works!")

if __name__ == "__main__":
    test_memory()
