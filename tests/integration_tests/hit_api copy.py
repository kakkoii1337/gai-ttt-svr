import asyncio
import httpx
import json

async def hit_api(json_payload):
    # Asynchronously send the POST request using httpx with streaming
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post("http://localhost:12031/gen/v1/chat/completions", json=json_payload)
        async for line in response.aiter_lines():
            # Ensure the line is not empty
            if line.strip():
                result = json.loads(line)
                # Simulate handling of the streamed response
                print({result["choices"][0]["delta"]["content"]},end="",flush=True)

# Generate the JSON payload
json_payload = {
    "temperature": 0.2,
    "max_new_tokens": 1000,
    "stream": True,
    "messages": [
        {
            "role": "user",
            "content": "Tell me a one paragraph story."
        },
        {
            "role": "assistant",
            "content": ""
        }
    ]
}

async def main():
    # Create a list of asyncio tasks
    tasks = [hit_api(json_payload) for _ in range(3)]
    # Run all tasks concurrently
    await asyncio.gather(*tasks)

# Execute the main async function
if __name__ == "__main__":
    asyncio.run(main())
