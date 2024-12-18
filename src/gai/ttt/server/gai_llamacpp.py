from gai.lib.common import generators_utils, logging
from gai.lib.common.generators_utils import apply_tools_message, get_tools_schema, format_list_to_prompt
from gai.lib.common.utils import get_app_path
import os,torch,gc,json
#from openai.types.chat.chat_completion import ChatCompletion, ChatCompletionMessage, Choice , CompletionUsage
#from openai.types.chat.chat_completion_chunk import ChatCompletionChunk, Choice as ChunkChoice, ChoiceDelta
from uuid import uuid4
from datetime import datetime
from typing import List
logger = logging.getLogger(__name__)
from llama_cpp import Llama, LlamaGrammar
# from gai.gen.ttt.OutputBuilder import OutputBuilder
# from gai.gen.ttt.ChunkOutputBuilder import ChunkOutputBuilder
from gai.lib.common.profile_function import profile_function
from gai.ttt.server.builders import CompletionsFactory
from gai.ttt.server.config.pydantic.ttt_config import TTTConfig

class GaiLlamaCpp:
    param_whitelist=[
        'max_tokens',
        'stopping_criteria',
        'temperature',
        'top_k',
        'top_p',
        'stream',
        'grammar',
        'json_schema'
        ]

    def __init__(self,llm_config:TTTConfig,verbose=True):
        if (llm_config is None):
            raise Exception("gai_llamacpp: gai_config is required")
        if llm_config.model_filepath is None:
            raise Exception("gai_llamacpp: model_filepath is required")
        self.__verbose=verbose
        self.gai_config = llm_config
        self.model_filepath = os.path.join(get_app_path(), llm_config.model_filepath)
        self.client = None

    def load(self):
        logger.info(f"gai_llamacpp.load: Loading model from {self.model_filepath}")
        self.client = Llama(model_path=self.model_filepath, verbose=False, n_ctx=self.gai_config.max_seq_len)
        self.client.verbose=False
        return self

    def unload(self):
        try:
            del self.client
        except :
            pass
        self.client = None
        gc.collect()
        torch.cuda.empty_cache()

    def token_count(self,text):
        #return len(self.client.tokenize(text.encode()))
        if isinstance(text,dict):
            text=json.dumps(text)
        elif isinstance(text,list):
            text=json.dumps(text)
        return len(self.client.tokenize(text.encode()))

    def is_using_tools(self,**kwargs):
        using_tools = kwargs["tool_choice"]=="required" and kwargs["tools"]
        return using_tools
    
    def is_using_json_schema(self,**kwargs):
        using_json_schema = ((kwargs["tool_choice"]=="none" or kwargs["tool_choice"]=="auto") and kwargs["json_schema"])
        return using_json_schema

    def create(self,
               messages:str | list,
               stream: bool=True,
               temperature:float=None, 
               top_k:float=None, 
               top_p:float=None,
               max_tokens:int=None,
               tools:dict=None,
               tool_choice:str='auto',
               json_schema:dict=None,
               stop:List[str]=None,
               seed:int=None):
        
        if not self.client:
            self.load()

        # temperature
        temperature=temperature or self.gai_config.hyperparameters.temperature
        # top_k
        top_k=top_k or self.gai_config.hyperparameters.top_k
        # top_p
        top_p=top_p or self.gai_config.hyperparameters.top_p
        # max_tokens
        max_tokens=max_tokens or self.gai_config.hyperparameters.max_tokens
        # stop
        stop=stop or self.gai_config.hyperparameters.stop

        # messages -> list
        if isinstance(messages,str):
            messages = generators_utils.chat_string_to_list(messages)
        self.messages=messages

        # tools
        if tools and tool_choice != "none":
            messages = apply_tools_message(messages=messages,tools=tools,tool_choice=tool_choice)
            json_schema= get_tools_schema()
            temperature=0

        # json_schema
        grammar = None
        if json_schema:
            grammar = LlamaGrammar.from_json_schema(json.dumps(json_schema))

        # Chat
        kwargs={
            "messages": messages,
            "temperature": temperature,
            "top_k": top_k,
            "top_p": top_p,
            "max_tokens": max_tokens,
            "grammar": grammar,
            "tools": tools,
            "stop": stop,
            "seed": seed,
            "stream": stream,
            "tool_choice": tool_choice,
        }
        if stream and not tools and not json_schema:
            response = (chunk for chunk in self.client.create_chat_completion(**kwargs))    
        response = self.client.create_chat_completion(**kwargs)

        # Convert Output
        factory = CompletionsFactory()        
        if not stream:
            if self.is_using_tools(**kwargs):
                logger.info(f"gai_llamacpp: factory.message.build_toolcall(response)")
                return factory.message.build_toolcall(response)
            else:
                logger.info(f"gai_llamacpp: factory.message.build_content(response)")
                return factory.message.build_content(response) 
        else:
            return (chunk for chunk in factory.chunk.build_stream(response))                           



