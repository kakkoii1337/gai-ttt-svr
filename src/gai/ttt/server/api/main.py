import json
import os

os.environ["LOG_LEVEL"]="DEBUG"
from gai.lib.common.logging import getLogger
logger = getLogger(__name__)
from dotenv import load_dotenv
load_dotenv()

# GAI
from gai.lib.common.errors import *
from gai.lib.server.api_dependencies import get_app_version

# Router
from pydantic import BaseModel
from typing import List, Optional
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi import APIRouter, Body, Depends
import uuid
import asyncio

router = APIRouter()
pyproject_toml = os.path.join(os.path.dirname(os.path.abspath(__file__)),"..", "..", "..", "..", "..", "pyproject.toml")

# Add this at the beginning, before your other routes
@router.get("/")
async def root():
    return JSONResponse(status_code=200, content={"message": "gai-ttt-svr-exllamav2"})

### ----------------- TTT ----------------- ###

# GET /gen/v1/chat/version
@router.get("/gen/v1/chat/version")
async def version():
    return JSONResponse(status_code=200, content={
        "version": get_app_version(pyproject_toml=pyproject_toml)
    })

# POST /gen/v1/chat/completions
class MessageRequest(BaseModel):
    role: str
    content: str
class ChatCompletionRequest(BaseModel):
    messages: List[MessageRequest]
    stream: Optional[bool] = False
    tools: Optional[list] = None
    tool_choice: Optional[str] = None
    json_schema: Optional[dict] = None    
    max_tokens: Optional[int] = None
    stop: Optional[list] = None
    temperature: Optional[float] = None
    top_p: Optional[float] = None
    top_k: Optional[int] = None

@router.post("/gen/v1/chat/completions")
async def post_chat_completions(req: ChatCompletionRequest = Body(...)):
    if req.stream:
        return StreamingResponse(process_stream(req), media_type="application/json")
    return await process_generate(req)

async def process_stream(req: ChatCompletionRequest):
    host = app.state.host
    response=None
    try:
        messages = req.messages
        response = host.generator.create(
            messages=[message.model_dump() for message in messages],
            stream=req.stream,
            tools=req.tools,
            tool_choice=req.tool_choice,
            json_schema=req.json_schema,
            max_tokens=req.max_tokens,
            stop=req.stop,
            temperature=req.temperature,
            top_p=req.top_p,
            top_k=req.top_k
        )
        for chunk in response:
            try:
                if chunk is not None:
                    print(chunk.choices[0].delta.content, end="", flush=True)
                    chunk = chunk.json() + "\n"
                    yield chunk
            except Exception as e:
                logger.warn(f"Error in stream: {e}")
                continue
    except Exception as e:
        if (str(e)=='context_length_exceeded'):
            raise ContextLengthExceededException()
        if (str(e)=='model_service_mismatch'):
            raise GeneratorMismatchException()
        id=str(uuid.uuid4())
        logger.error(str(e)+f" id={id}")
        raise InternalException(id)

async def process_generate(req: ChatCompletionRequest):
    host = app.state.host
    response=None
    
    try:
        messages = req.messages
        response = host.generator.create(
            messages=[message.model_dump() for message in messages],
            stream=req.stream,
            tools=req.tools,
            tool_choice=req.tool_choice,
            json_schema=req.json_schema,
            max_tokens=req.max_tokens,
            stop=req.stop,
            temperature=req.temperature,
            top_p=req.top_p,
            top_k=req.top_k
        )
        return response
    except Exception as e:
        if (str(e)=='context_length_exceeded'):
            raise ContextLengthExceededException()
        if (str(e)=='model_service_mismatch'):
            raise GeneratorMismatchException()
        id=str(uuid.uuid4())
        logger.error(str(e)+f" id={id}")
        raise InternalException(id)

# __main__
if __name__ == "__main__":

    import uvicorn
    from gai.lib.server import api_factory
    from gai.ttt.server.config.config_utils import get_gai_config

    gai_config = get_gai_config()
    ttt_config = gai_config.ttt.configs[gai_config.ttt.default]

    # Log hyperparameters
    logger.info("Hyperparameters:")
    logger.info(ttt_config.hyperparameters)
    logger.info(f"\tmax_seq_len\t: {ttt_config.max_seq_len}")

    app = api_factory.create_app(pyproject_toml, category="ttt",llm_config=ttt_config)
    app.include_router(router, dependencies=[Depends(lambda: app.state.host)])
    config = uvicorn.Config(
        app=app, 
        host="0.0.0.0", 
        port=12031, 
        timeout_keep_alive=180,
        timeout_notify=150,
        workers=1
    )
    server = uvicorn.Server(config=config)
    server.run()
