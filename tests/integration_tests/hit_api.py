import asyncio
import httpx
import json

async def make_request(client, json_payload, idx):
    url = "http://localhost:8000/gen/v1/chat/completions"
    async with client.stream("POST", url, json=json_payload, timeout=60) as response:
        response.raise_for_status()
        try:
            async for chunk in response.aiter_raw():
                if chunk:
                    print(chunk.decode(),end="",flush=True)
        except json.JSONDecodeError as e:
            print(f"JSON decode error in response {idx}: {e} - Line received: '{line}'")
        except Exception as e:
            print(f"General error in response {idx}: {e}")
    print(f"\nRequest {idx} completed.\n")


async def main():
    # Define the JSON payload
    json_payload = {
        "temperature": 0.2,
        "max_new_tokens": 1000,
        "stream": True,
        "messages": [
            {"role": "user", "content": "Tell me a one paragraph story."},
            {"role": "assistant", "content": ""}
        ]
    }

    # Create an HTTPX client
    async with httpx.AsyncClient() as client:
        # Create tasks for simultaneous requests
        tasks = [make_request(client, json_payload, idx) for idx in range(1, 4)]
        # Execute tasks concurrently
        await asyncio.gather(*tasks)

if __name__ == "__main__":
    asyncio.run(main())
