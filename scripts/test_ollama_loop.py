import asyncio
import httpx
import json

async def simulate():
    tools = [{
        "type": "function",
        "function": {
            "name": "push_to_canvas",
            "description": "Push content to canvas",
            "parameters": {
                "type": "object",
                "properties": {"mode": {"type": "string"}, "content": {"type": "string"}},
                "required": ["mode", "content"]
            }
        }
    }]
    
    messages = [{"role": "user", "content": "Create a simple page and push it to canvas."}]
    
    async with httpx.AsyncClient() as client:
        print("--- Loop 1 ---")
        resp = await client.post("http://localhost:11434/api/chat", json={
            "model": "qwen3.5:27b",
            "messages": messages,
            "stream": False,
            "tools": tools
        })
        data = resp.json()
        msg = data["message"]
        print("Assistant returned:", msg)
        
        if msg.get("tool_calls"):
            messages.append(msg)
            for tc in msg["tool_calls"]:
                messages.append({
                    "role": "tool",
                    "name": tc["function"]["name"],
                    "content": "Success!"
                })
                
        print("\n--- Loop 2 ---")
        resp2 = await client.post("http://localhost:11434/api/chat", json={
            "model": "qwen3.5:27b",
            "messages": messages,
            "stream": False,
            "tools": tools
        })
        data2 = resp2.json()
        print("Assistant returned in loop 2:", data2["message"])

asyncio.run(simulate())
