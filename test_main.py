import subprocess
import time

def test_interactive():
    print("Starting interactive test...")
    # Run the main.py script
    process = subprocess.Popen(
        ['/home/scruffydawg/gemini_workspace/ai_agent_platform/venv/bin/python3', 'src/main.py'],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        env={"PYTHONPATH": "/home/scruffydawg/gemini_workspace/ai_agent_platform"}
    )
    
    # Wait for startup
    time.sleep(1)
    
    # Send a prompt to orchestrated
    print("Testing prompt routing...")
    process.stdin.write("Please research this.\n")
    process.stdin.flush()
    time.sleep(2)
    
    # Trigger kill switch via Enter key
    print("Testing Kill Switch...")
    process.stdin.write("\n")
    process.stdin.flush()
    time.sleep(1)
    
    stdout, stderr = process.communicate()
    
    if "Kill Switch is active" in stdout or "Halted" in stdout:
        print("Success: System Halted via Kill Switch.")
    else:
        print("Failed: System did not halt as expected.")
        print(f"Stdout:\n{stdout}")
        print(f"Stderr:\n{stderr}")

if __name__ == "__main__":
    test_interactive()
