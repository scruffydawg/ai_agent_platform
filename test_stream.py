import httpx
import asyncio

async def main():
    try:
        async with httpx.AsyncClient() as client:
            async with client.stream("POST", "http://localhost:8001/api/v2/chat", json={"prompt": "Hello"}) as response:
                print(f"Status: {response.status_code}")
                try:
                    async for chunk in response.aiter_text():
                        print(f"CHUNK: {repr(chunk)}")
                except Exception as stream_e:
                    print(f"Stream error: {repr(stream_e)}")
    except Exception as e:
        print(f"Request Error: {repr(e)}")

asyncio.run(main())
