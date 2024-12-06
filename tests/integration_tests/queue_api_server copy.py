from fastapi import FastAPI, APIRouter, Body, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import List, Optional
import asyncio
import uuid
import json

app = FastAPI()
router = APIRouter()
request_queue = asyncio.Queue()
processing_semaphore = asyncio.Semaphore(1)  # Ensure only one task is processed at a time

class MessageRequest(BaseModel):
    role: str
    content: str

class ChatCompletionRequest(BaseModel):
    messages: List[MessageRequest]
    stream: bool = False

@router.post("/gen/v1/chat/completions")
async def chat_completions(req: ChatCompletionRequest = Body(...)):
    req_id = uuid.uuid4()
    await request_queue.put((req, req_id))
    if req.stream:
        return StreamingResponse(process_stream(req_id), media_type="application/json")
    return {"message": "Request queued", "id": str(req_id)}

async def process_stream(req_id):
    from gai.lib.server.singleton_host import SingletonHost

    config = {
        "type": "ttt",
        "generator_name": "exllamav2-mistral7b",
        "engine": "gai.ttt.server.GaiExLlamaV2",
        "model_path": "models/exllamav2-dolphin",
        "model_basename": "model",
        "max_seq_len": 8192,
        "prompt_format": "mistral",
        "hyperparameters": {
            "temperature": 0.85,
            "top_p": 0.8,
            "top_k": 50,
            "max_tokens": 1000,
        },
        "tool_choice": "auto",
        "max_retries": 5,
        "stop_conditions": ["<|im_end|>", "</s>", "[/INST]"],
        "no_flash_attn":True,
        "seed": None,
        "decode_special_tokens": False,
        "module_name": "gai.ttt.server.gai_exllamav2",
        "class_name": "GaiExLlamav2",
        "init_args": [],
        "init_kwargs": {}
    }
    # story=""
    with SingletonHost.GetInstanceFromConfig(config,verbose=False) as host:
        response = host.generator.create(
            messages=[{"role":"user","content":"Tell me a one paragraph story"},
                        {"role":"assistant","content":""}],
            stream=True)
        for message in response:
            if message.choices[0].delta.content:
                yield message.choices[0].delta.content
                print(message.choices[0].delta.content, end="", flush=True)

@app.on_event("startup")
async def startup_event():
    task = asyncio.create_task(process_queue())

async def process_queue():
    while True:
        await processing_semaphore.acquire()
        try:
            req, req_id = await request_queue.get()
        finally:
            processing_semaphore.release()

app.include_router(router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
