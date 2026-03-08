import time
from heartbeat import heartbeat
from state import state_manager

def dummy_task():
    print("[Task] Triggered.")

def test():
    # Register task
    heartbeat.register_task("dummy", dummy_task)
    
    # Start heartbeat
    heartbeat.start()
    print("Heartbeat started. Listening...")
    
    # Wait to see triggers
    time.sleep(3)
    
    # Trigger global kill switch
    print("Triggering kill switch...")
    state_manager.trigger_halt("Test run completed.")
    
    # Wait to ensure heartbeat stopped
    time.sleep(2)
    
    if not heartbeat._running:
        print("Success: Heartbeat and Kill Switch functioning as intended.")
    else:
        print("Error: Heartbeat did not stop.")

if __name__ == "__main__":
    test()
