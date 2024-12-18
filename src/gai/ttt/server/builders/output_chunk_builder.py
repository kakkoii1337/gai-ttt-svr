from openai.types.chat.chat_completion_chunk import ChatCompletionChunk, Choice as ChunkChoice, ChoiceDelta
from openai.types.chat.chat_completion_chunk import ChoiceDeltaToolCall, ChoiceDeltaToolCallFunction
from datetime import datetime
from uuid import uuid4

class OutputChunkBuilder:

    def build_content(self,result,generator_name="llamacpp"):
        if (result is None):
            return None

        finish_reason = result["choices"][0]["finish_reason"]
        content = result["choices"][0]["delta"].get("content",None)

        if (content is None):
            return OutputChunkBuilder(
                ).add_chunk(generator=generator_name
                    ).add_chunk_choice_delta(finish_reason=None, role="assistant"
                        ).add_chunk_choice_delta_content(content=''
                            ).build()

        if (type(content) is str):
            return OutputChunkBuilder(
                ).add_chunk(generator=generator_name
                    ).add_chunk_choice_delta(finish_reason=None, role=None
                        ).add_chunk_choice_delta_content(content=content
                            ).build()

        if (finish_reason):
            return OutputChunkBuilder(
                ).add_chunk(generator=generator_name
                    ).add_chunk_choice_delta(finish_reason=finish_reason, role=None
                        ).build()

    def build_stream(self,streaming_response):
        def streamer():
            head =  self.build_content(None)
            yield head
            for chunk in streaming_response:
                yield self.build_content(chunk)
        return (chunk for chunk in streamer())

    def __init__(self, result=None):
        self.result = None
        if result:
            self.result = result.copy()

    def copy(self):
        return OutputChunkBuilder(self.result)

    def generate_chatcompletion_id(self):
        return "chatcmpl-"+str(uuid4())

    def generate_creationtime(self):
        return int(datetime.now().timestamp())

    def generate_toolCall_id(self):
        return "call_"+str(uuid4())

    def add_chunk(self,generator):
        chatcompletion_id = self.generate_chatcompletion_id()
        created = self.generate_creationtime()
        self.result = ChatCompletionChunk(
            id=chatcompletion_id,
            choices=[],
            created=created,
            model=generator,
            object='chat.completion.chunk'
        )
        return self

    def add_chunk_choice_delta(self, role=None, finish_reason=None):
        self.result.choices.append(
            ChunkChoice(
                delta=ChoiceDelta(
                    content=None, 
                    role=role, 
                    tool_calls=None, 
                    function_call=None
                    ),
                index=0,
                logprobs=None,
                finish_reason=finish_reason,
            )            
        )
        return self

    def add_chunk_choice_delta_content(self, content):
        self.result.choices[0].delta.content=content
        return self

    def add_chunk_choice_delta_toolcall_name(self, name):
        self.result.choices[0].delta.tool_calls=[ChoiceDeltaToolCall(
            index=0,
            id=self.generate_toolCall_id(),
            function=ChoiceDeltaToolCallFunction(
                name=name,
                arguments=''
                ),
            type='function'
            )]
        return self

    def add_chunk_choice_delta_toolcall_arguments(self, arguments):
        self.result.choices[0].delta.tool_calls=[ChoiceDeltaToolCall(
            index=0,
            id=None,
            function=ChoiceDeltaToolCallFunction(
                name=None,
                arguments=arguments
                ),
            type='function'
            )]
        return self
    
    def build(self):
        return self.result.copy()

