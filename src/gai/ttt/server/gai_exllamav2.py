import os,torch,gc,json
from typing import Optional
from gai.lib.common.utils import get_app_path
from gai.lib.common.logging import getLogger
logger = getLogger(__name__)
from jsonschema import validate, ValidationError
from gai.lib.common.profile_function import profile_function
from gai.ttt.server.builders import CompletionsFactory

def correct_single_quote_json(s):
    rstr = ""
    escaped = False

    # Remove single quotes at the beginning and end of the string
    s=s.strip("'")

    for c in s:
    
        if c == "'" and not escaped:
            c = '"' # replace single with double quote
        
        elif c == "'" and escaped:
            rstr = rstr[:-1] # remove escape character before single quotes
        
        elif c == '"':
            c = '\\' + c # escape existing double quotes

        escaped = (c == "\\") # check for an escape character
        rstr += c # append the correct json
    
    return rstr

class GaiExLlamav2:

    def __init__(self, gai_config, verbose=True):
        if (gai_config is None):
            raise Exception("GaiExLlamav2: gai_config is required")
        if gai_config.get("model_path",None) is None:
            raise Exception("GaiExLlamav2: model_path is required")
        self.__verbose=verbose
        self.gai_config = gai_config

        self.model_dir = os.path.join(get_app_path(
        ), gai_config["model_path"])
        self.cache = None
        self.model = None
        self.tokenizer = None
        self.prompt = None
        self.generator = None
    
    def __enter__(self):
        self.load()
        return self
    
    def __exit__(self,exc_type, exc_value,traceback):
        self.unload()
        gc.collect()
        torch.cuda.empty_cache()


    @profile_function
    def load_config(self):
        from exllamav2 import ExLlamaV2Config
        config=ExLlamaV2Config()
        config.model_dir = self.model_dir
        config.prepare()
        config.max_seq_len = self.gai_config.get("max_seq_len",8192)
        config.no_flash_attn = self.gai_config.get("no_flash_attn",True)
        self.exllama_config = config

    @profile_function
    def load_model(self):
        from exllamav2 import ExLlamaV2
        self.model = ExLlamaV2(self.exllama_config)
    
    @profile_function    
    def load_cache(self):
        from exllamav2.cache import ExLlamaV2Cache_Q4
        self.cache = ExLlamaV2Cache_Q4(self.model, 
                                       lazy=True, 
                                       max_seq_len=self.gai_config.get("max_seq_len",8192))
        self.model.load_autosplit(self.cache)

    @profile_function
    def load_tokenizer(self):
        from exllamav2 import ExLlamaV2Tokenizer
        self.tokenizer = ExLlamaV2Tokenizer(self.exllama_config)

    @profile_function
    def load_generator(self):
        from exllamav2.generator import ExLlamaV2DynamicGenerator

        # Note: Dynamic Generator requires flash-attn 2.5.7+ to use paged attention and only supports Ampere GPUs or newer, otherwise set paged=False
        self.generator=ExLlamaV2DynamicGenerator(model=self.model, 
                                            cache=self.cache, 
                                            tokenizer=self.tokenizer,
                                            paged=False)
        self.generator.warmup()

    # initial load
    def load(self):
        self.load_config(verbose=self.__verbose)
        self.load_model(verbose=self.__verbose)
        self.load_cache(verbose=self.__verbose)
        self.load_tokenizer(verbose=self.__verbose)

    def unload(self):
        if self.generator is not None:
            del self.model
            del self.cache
            del self.tokenizer
            del self.generator
            import gc,torch
            gc.collect()
            torch.cuda.empty_cache()
        return self

    # Configure JSON Schema enforcement for tool call and response model
    def prepare_filters(self, tools, tool_choice, json_schema):
        """
        1. tool_choice always takes precedence over schema.
           If schema is required, then tool_choice must be set to "none".
        2. If tool_choice is "auto", then tools schema will always be used but tools will include { "type": "text", "text": "..." }.
        3. If tool_choice is "required", then tools schema will always be used and tools will not include { "type": "text", "text": "..." }.
        4. If tool_choice is "none", then schema will be used if it is available.
        5. If tool_choice is "none" and schema is not available then output will always be text.
        6. If tool_choice is "none" and schema is available then output will always be based on schema, aka. JSON mode.        
        """

        self.validation_schema=None

        # Create filter from schema
        from lmformatenforcer import JsonSchemaParser
        from lmformatenforcer.integrations.exllamav2 import build_token_enforcer_tokenizer_data, ExLlamaV2TokenEnforcerFilter
        from exllamav2.generator.filters.prefix import ExLlamaV2PrefixFilter

        if not tools and tool_choice=="required":
            raise Exception("tool_choice='required' requires tools to be provided.")
        
        if (not self.is_validation_required(self.job_state)):
            self.validation_schema=None
            return None        

        if (self.is_using_tools(self.job_state)):
            # If toolcall is used, use toolcall schema and create filters for it
            #from gai.lib.common.generators_utils import get_tools_schema
            def get_tools_schema():
                return {
                    "type": "object",
                    "properties": {
                        "function": {
                            "type": "object",
                            "properties": {
                                "name": {
                                    "type": "string"
                                },
                                "arguments": {
                                    "type": "object",
                                }
                            },
                            "required": ["name", "arguments"]
                        },
                    },
                    "required": ["function"],
                    "additionalProperties": True
                }

            self.validation_schema=get_tools_schema()
            tokenizer_data = build_token_enforcer_tokenizer_data(self.tokenizer)
            parser = JsonSchemaParser(self.validation_schema)
            return [ExLlamaV2PrefixFilter(self.model, self.tokenizer, ['{"function":']), ExLlamaV2TokenEnforcerFilter(parser, tokenizer_data)]

        if (self.is_using_json_schema(self.job_state)):
            # If user_defined schema, apply user_defined schema
            self.validation_schema=json_schema
            tokenizer_data = build_token_enforcer_tokenizer_data(self.tokenizer)
            parser = JsonSchemaParser(self.validation_schema)
            return [ExLlamaV2TokenEnforcerFilter(parser, tokenizer_data)]

    # Configure intermediate prompts for tool call and response model formatted for the underlying LLM
    def prepare_prompt(self, messages, json_schema, tools, tool_choice, stream):
        final_formatted_messages=[]
        formatted_messages = messages.copy()

        def has_ai_placeholder(messages):
            message = messages[-1]
            if message["role"].lower() != "system" and message["role"].lower() != "user" and message["content"] == "":
                return True
            return False

        def merge_system_messages(messages, system_message):
            last_system_message_index = -1
            i = len(messages) - 1
            # merge system messages from the back to front
            while i >= 0:
                if messages[i]["role"].lower() == "system":
                    if last_system_message_index == -1:
                        # first system message from the back found
                        last_system_message_index = i
                        messages[i]["content"] += " " + system_message['content']
                    else:
                        # next system message from the back found
                        messages[i]["content"] += " " + messages[last_system_message_index]['content']
                        messages.pop(last_system_message_index)
                        last_system_message_index = i
                i -= 1
            if last_system_message_index == -1:
                # no system message found
                messages.insert(0,system_message)
            return messages


        if (self.is_using_tools(self.job_state)):

            def apply_tools_message( messages: list, tools:dict, tool_choice:str):
                # Proceed only if tools are available
                if not tools:
                    return messages

                # Check if tools are required and add a tools prompt
                if tools:

                    if tool_choice == "none":
                        # If tool_choice == "none", skip adding tools
                        return messages
                    
                    if tool_choice == "required":
                        # Create a system message to introduce the tools
                        system_message = {"role":"system","content":
                        """
                        1. Respond to the user's message using only JSON object according to the schema below.
                            {tools}
                        2. Begin your response with an open curly brace '{{'.
                        3. End your response with a closing curly brace '}}'.
                        4. For example:
                            {{
                                "function": {{
                                    "name": "tool_name",
                                    "arguments": {{
                                        "key": "value"
                                    }}
                                }}
                            }}
                        """}   

                    # When tool_choice == "auto", the system can return a tool response
                    # or a text response. It is difficult to rely on local models to handle "auto" so it is better to use "required" in mult-turn.
                    if tool_choice == "auto":

                        # Create a system message to introduce the tools
                        system_message = {"role":"system","content":
                        """
                        1. Review the <tools> below and assess if any of them is suitable for responding to the user's message.

                            {tools}

                        2. If none of the tools are suitable, you can respond with a <text> response that looks like the following:
                            
                        {{
                            "function": {{
                                "name": "text",
                                "arguments": {{
                                    "text": "This is a text response."
                                }}
                            }}
                        }}"""}

                    # Create system_message
                    system_message["content"] = system_message["content"].format(
                        tools=tools)

                    # Merge all system messages
                    messages=merge_system_messages(messages, system_message)

                return messages

            # Add system_message for tool_call
            #from gai.lib.common.generators_utils import apply_tools_message
            formatted_messages = apply_tools_message(messages=formatted_messages,
                tools=tools,
                tool_choice=tool_choice)
        else:
            formatted_messages = formatted_messages
            
        if (self.is_using_json_schema(self.job_state)):

            # Add system_message to use schema (response model) if tool_call are not applicable
            from gai.lib.common.generators_utils import apply_schema_prompt
            from typing import List

            def apply_schema_prompt( messages: List, schema):

                # Apply schema. Note that tool schema will override any provided schema.
                if schema:
                    system_message={"role":"system","content":f"""Begin your response with an open curly brace. Your response must be parseable by this json schema: {schema} """}
                    #system_message={"role":"system","content":f"You will respond to the user's message based only on the following JSON schema {schema}. Begin your response with a curly bracket '{{' and end it with a curly bracket '}}'."}

                    # Merge the schema prompt with the last system message instead of having an extra system message
                    messages = merge_system_messages(messages, system_message)

                return messages

            formatted_messages = apply_schema_prompt(messages=formatted_messages, schema=json_schema)

        else:
            formatted_messages = formatted_messages

        # prompt_format = self.gai_config.get("prompt_format")
        # from gai.lib.common.generators_utils import format_list_to_prompt
        # prompt = format_list_to_prompt(messages=formatted_messages, format_type=prompt_format, stream=stream)

        # prompt="<s>[INST] "
        # for message in formatted_messages:
        #     role = message['role']
        #     content = message['content']
        #     if content:
        #         prompt+=f"{role}: {content}\n"
        #     else:
        #         prompt+=f"[/INST]{role}:"

        prompt=""
        for message in formatted_messages:
            role = message['role']
            content = message['content']
            if content:
                prompt+=f"<|im_start|> {role}\n {content}<|im_end|>\n"
            else:
                if role == "assistant":
                    prompt+=f"<|im_start|> {role}\n "
                    break

        return prompt
    
    def is_validation_required(self,job_state):
        return self.is_using_tools(job_state) or self.is_using_json_schema(job_state)

    # tools are only used when tool_choice is "required" and tools are available
    def is_using_tools(self,job_state):
        using_tools = (job_state["tool_choice"]=="required" and job_state["tools"])
        return using_tools

    # response model is only used when tool_choice is none and json_schema is available
    def is_using_json_schema(self,job_state):
        using_json_schema = ((job_state["tool_choice"]=="none" or job_state["tool_choice"]=="auto") and job_state["json_schema"])
        return using_json_schema

    @profile_function
    def generate(self):

        eos = False
        while not eos:
            results = self.generator.iterate()
            for result in results:
                eos=result.get("eos",False)
        return result
    
    def find_function_object(self,json_data):
        """
        Recursively searches for a dictionary that contains both 'name' and 'arguments' keys within nested JSON.
        
        :param json_data: The JSON data to search through.
        :return: The dictionary that contains 'name' and 'arguments' keys or None if not found.
        """
        if isinstance(json_data, dict):  # If the current data is a dictionary

            # Check if the dictionary has both 'name' and 'arguments' keys
            if 'name' in json_data and 'arguments' in json_data:
                arguments = json_data['arguments']
                # check if arguments is a key value pair dictionary
                if isinstance(arguments, dict):
                    for key in arguments:
                        # Do not support nested dictionaries in the arguments
                        if isinstance(arguments[key], dict):
                            return None

                # found
                return {'name': json_data['name'], 'arguments': arguments}

            # or 'name' and 'parameters' keys
            if 'name' in json_data and 'parameters' in json_data:
                arguments = json_data['parameters']
                # check if parameters is a key value pair dictionary
                if isinstance(arguments, dict):
                    for key in arguments:
                        # Do not support nested dictionaries in the arguments
                        if isinstance(arguments[key], dict):
                            return None
                # found
                return {'name': json_data['name'], 'arguments': arguments}

            # of 'function' and 'arguments' keys
            if 'function' in json_data and 'arguments' in json_data:
                
                # check if function is a string
                if not isinstance(json_data['function'],str):
                    return None

                arguments = json_data['arguments']
                # check if arguments is a key value pair dictionary
                if isinstance(arguments, dict):
                    for key in arguments:
                        # Do not support nested dictionaries in the arguments
                        if isinstance(arguments[key], dict):
                            return None
                # found
                return {'name': json_data['function'], 'arguments': arguments}       

            # of 'function' and 'parameters' keys
            if 'function' in json_data and 'parameters' in json_data:
                
                # check if function is a string
                if not isinstance(json_data['function'],str):
                    return None

                arguments = json_data['parameters']
                # check if parameters is a key value pair dictionary
                if isinstance(arguments, dict):
                    for key in arguments:
                        # Do not support nested dictionaries in the arguments
                        if isinstance(arguments[key], dict):
                            return None
                # found
                return {'name': json_data['function'], 'arguments': arguments}            

            # Otherwise, iterate over the values and continue the search
            for key in json_data:
                result = self.find_function_object(json_data[key])
                if result:
                    return result

        elif isinstance(json_data, list):  # If the current data is a list
            # Iterate over each item in the list and continue the search
            for item in json_data:
                result = self.find_function_object(item)
                if result:
                    return result
                
        return None  # Return None if no matching dictionary is found

    # Retry completions if validation is required
    def _generate_with_retries(self):
        retries=self.job_state["max_retries"]

        # Validation not required
        if not self.is_validation_required(self.job_state):
            return self.generate(verbose=self.__verbose)
        
        # Validation required
        while retries>0:
            result=self.generate(verbose=self.__verbose)
            try:
                if (self.is_using_tools(self.job_state)):
                    # This will throw error if its not even JSON
                    jsoned=json.loads(result["full_completion"])
                    logger.debug(f"gai_exllamav2._generate_with_retries: json validated = {jsoned}")

                    # Instead of using schema validation to validate the structured output for tool call, 
                    # use heuristics to find the object that contains "name" and "arguments" only 
                    # and hack it to relax the search.
                    jsoned = self.find_function_object(jsoned)
                    if not jsoned:
                        raise ValidationError("Failed tool call output validation.")
                    result["full_completion"] = json.dumps({
                        "function": jsoned
                    })

                if (self.is_using_json_schema(self.job_state)):
                    # This will throw error if its not even JSON
                    jsoned=json.loads(result["full_completion"])

                    # This will throw error if its JSON but schema is invalid
                    validate(instance=jsoned, schema=self.validation_schema)

                # We are safe once we reach here since its either text or we have passed validations
                return result
            except ValidationError as e:
                logger.error(f"GaiExLlamav2.generate_with_retries: \nCan parse JSON but failed tool_call validation: {jsoned}. error={e} result={result} prompt={self.prompt}")
                retries-=1
                self.load_job()
            except Exception as e:
                logger.error(f"GaiExLlamav2.generate_with_retries: error={e} result={result} prompt={self.prompt}")
                retries-=1
                self.load_job()
        raise Exception("GaiExLlamav2.generate_with_retries: Validation of schema is required and failed after max retries.")

    def _streaming(self):
        eos = False
        result = None
        completed = ""

        while not eos:

            # Run one iteration of the generator. Returns a list of results
            results = self.generator.iterate()
            for result in results:
                text=result.get("text","")
                if text:
                    completed+=text
                    yield text
                eos=result.get("eos",False)
        
        if eos:
            logger.info(f"gai_exllamav2._streaming: result={result}")

        yield result

    def load_job(self):

        from exllamav2.generator import ExLlamaV2Sampler
        settings = ExLlamaV2Sampler.Settings()
        settings.temperature=self.job_state["temperature"]
        settings.top_k=self.job_state["top_k"]
        settings.top_p=self.job_state["top_p"]

        # Prepare settings.filters
        from exllamav2.generator import ExLlamaV2DynamicJob
        settings.filters = self.prepare_filters(tools=self.job_state["tools"], 
                                                     tool_choice=self.job_state["tool_choice"],
                                                     json_schema=self.job_state["json_schema"])
        if settings.filters:
            logger.info(f"GaiExLlamav2.load_job: apply filters.")
            settings.temperature=0

        import copy
        messages = copy.deepcopy(self.job_state["messages"])

        self.prompt=self.prepare_prompt(messages=messages,
                                   json_schema=self.job_state["json_schema"],
                                   tools=self.job_state["tools"],
                                   tool_choice=self.job_state["tool_choice"],
                                   stream=True)
        logger.debug(f"GaiExLlamav2.load_job: prompt={self.prompt}")

        max_tokens=self.job_state["max_tokens"]
        logger.debug(f"GaiExLlamav2.load_job: max_tokens={max_tokens}")

        stop_conditions=self.job_state["stop_conditions"]
        logger.debug(f"GaiExLlamav2.load_job: stop_conditions={stop_conditions}")
        
        logger.debug(f"GaiExLlamav2.load_job: temperature={settings.temperature}")

        # Reset generator and run job
        self.job = ExLlamaV2DynamicJob(    
            input_ids = self.tokenizer.encode(self.prompt),
            gen_settings = settings,
            max_new_tokens = max_tokens,
            completion_only = True,
            token_healing = True,
            seed = None,
            stop_conditions=stop_conditions,
            add_bos=False,
            #encode_special_tokens=self.job_state["encode_special_tokens"],
            decode_special_tokens=self.job_state["decode_special_tokens"],
        )
        # for pending in self.generator.pending_jobs:
        #     self.generator.cancel(pending)
        self.generator.enqueue(self.job)
        return self.generator               

    # Main driver for completions that calls _generate and _streaming,
    # but only return pure dictionary as output
    # Parameters are captured into a job_state for completions.
    def _create(self):
        try:
            self.load_job()
        except Exception as e:
            logger.error(f"GaiExLlamav2._create: Error loading job. error={e}")

        if not self.job_state["stream"]:
            return self._generate_with_retries()
        return (chunk for chunk in self._streaming())

    def initialize_job_state(self,
        messages:list,
        stream:Optional[bool], 
        tools:Optional[list]=None,
        tool_choice:Optional[str]=None,
        json_schema=None,
        max_tokens:Optional[int]=None,
        stop_conditions:Optional[list]=None,
        temperature:Optional[float]=None,
        top_p:Optional[float]=None,
        top_k:Optional[int]=None,
        max_retries:int=None
        ):
        logger.info("gai_exllamav2.create: Initializing job_state.")

        if self.tokenizer.eos_token_id not in self.gai_config["stop_conditions"]:
            self.gai_config["stop_conditions"].append(self.tokenizer.eos_token_id)
        for stop_condition in stop_conditions or []:
            if stop_condition not in self.gai_config["stop_conditions"]:
                self.gai_config["stop_conditions"].append(stop_condition)

        self.job_state = {
            "messages": messages,
            "stream": stream,
            "tools": tools,
            "json_schema": json_schema,
            "tool_choice": tool_choice or self.gai_config["tool_choice"],
            "stop_conditions": self.gai_config["stop_conditions"],
            "prompt_format": self.gai_config["prompt_format"],
            "max_tokens": max_tokens or self.gai_config["hyperparameters"]["max_tokens"],
            "temperature": temperature or self.gai_config["hyperparameters"]["temperature"],
            "top_p": top_p or self.gai_config["hyperparameters"]["top_p"],
            "top_k": top_k or self.gai_config["hyperparameters"]["top_k"],  
            "max_retries": max_retries or self.gai_config["max_retries"],
            "decode_special_tokens": self.gai_config["decode_special_tokens"]
        }
        if self.is_validation_required(self.job_state):
            if self.job_state["stream"]:
                raise Exception("GaiExLlamav2._streaming: Validation of schema is required and not supported in streaming mode.")
            self.job_state["temperature"]=0

    def create(self, 
        messages:list,
        stream:Optional[bool], 
        tools:Optional[list]=None,
        tool_choice:Optional[str]=None,
        json_schema=None,
        max_tokens:Optional[int]=None,
        stop_conditions:Optional[list]=None,
        temperature:Optional[float]=None,
        top_p:Optional[float]=None,
        top_k:Optional[int]=None,
        max_retries:int=None
        ):
        self.load_generator(verbose=self.__verbose)

        self.initialize_job_state(
            messages=messages,
            stream=stream,
            tools=tools,
            tool_choice=tool_choice,
            json_schema=json_schema,
            max_tokens=max_tokens,
            stop_conditions=stop_conditions,
            temperature=temperature,
            top_p=top_p,
            top_k=top_k,
            max_retries=max_retries
        )

        # Create completions
        response=self._create()

        # Convert Output
        factory = CompletionsFactory()        
        if not stream:
            if self.is_using_tools(self.job_state):
                logger.info(f"gai_exllamav2: factory.message.build_toolcall(response)")
                output=factory.message.build_toolcall(response)
                return output
            else:
                logger.info(f"gai_exllamav2: factory.message.build_content(response)")
                return factory.message.build_content(response)
        else:
            return (chunk for chunk in factory.chunk.build_stream(response))



