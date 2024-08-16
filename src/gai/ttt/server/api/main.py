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

router = APIRouter()
pyproject_toml = os.path.join(os.path.dirname(os.path.abspath(__file__)),"..", "..", "..", "..", "..", "pyproject.toml")

### ----------------- TTS ----------------- ###

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
    response_model: Optional[dict] = None    
    max_new_tokens: Optional[int] = None
    stop_conditions: Optional[list] = None
    temperature: Optional[float] = None
    top_p: Optional[float] = None
    top_k: Optional[int] = None

@router.post("/gen/v1/chat/completions")
async def _text_to_text(req: ChatCompletionRequest = Body(...)):
    host = app.state.host
    response=None
    try:
        messages = req.messages
        response = host.generator.create(
            messages=[message.model_dump() for message in messages],
            stream=req.stream,
            tools=req.tools,
            tool_choice=req.tool_choice,
            response_model=req.response_model,
            max_new_tokens=req.max_new_tokens,
            stop_conditions=req.stop_conditions,
            temperature=req.temperature,
            top_p=req.top_p,
            top_k=req.top_k
        )
        if req.stream:
            def streamer():
                for chunk in response:
                    try:
                        if chunk is not None:
                            chunk = jsonable_encoder(chunk)
                            chunk = json.dumps(chunk) + "\n"
                            yield chunk
                    except Exception as e:
                        logger.warn(f"Error in stream: {e}")
                        continue

            return StreamingResponse(streamer())
        else:
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

    # Run self-test before anything else
    import os
    if os.environ.get("SELF_TEST",None):
        self_test_file=os.path.join(os.path.dirname(os.path.abspath(__file__)),"self-test.py")
        import subprocess,sys
        try:
            subprocess.run([f"python {self_test_file}"],shell=True,check=True)
        except subprocess.CalledProcessError as e:
            sys.exit(1)
        ## passed self-test

    import uvicorn
    from gai.lib.server import api_factory
    app = api_factory.create_app(pyproject_toml, category="ttt")
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
