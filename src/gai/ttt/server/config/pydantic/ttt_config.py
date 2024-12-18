from typing import List, Dict, Optional, Any
from pydantic import BaseModel, Field
import yaml
from gai.lib.config.pydantic.gai_config import ServerLLMConfigBase

# ---------------------------
# Pydantic Models
# ---------------------------

# Shared Hyperparameters Schema
class Hyperparameters(BaseModel):
    temperature: float
    top_p: float
    top_k: int
    max_tokens: int
    tool_choice: Optional[str] = None
    max_retries: Optional[int] = None
    stop: Optional[List[str]] = None

# Extra Settings for Some Engines
class ExtraConfig(BaseModel):
    no_flash_attn: Optional[bool] = None
    seed: Optional[Any] = None
    decode_special_tokens: Optional[bool] = None
    
class ModuleConfig(BaseModel):
    name: str
    class_: str = Field(alias="class")  # Use 'class' as an alias for 'class_'

    class Config:
        allow_population_by_name = True  # Allow access via both 'class' and 'class_'

# Schema for TTT Configurations
class TTTConfig(ServerLLMConfigBase):
    model_filepath: Optional[str] = None
    model_path: Optional[str] = None
    model_basename: Optional[str] = None
    max_seq_len: int
    prompt_format: str
    hyperparameters: Hyperparameters
    extra: Optional[ExtraConfig] = None

class TTTSpecConfig(BaseModel):
    default: str=None
    configs: Optional[Dict[str,TTTConfig]]={}

class ServerConfig(BaseModel):
    ttt: TTTSpecConfig
        
    @classmethod
    def from_config(cls, config: dict):
        # Preprocess the config and initialize the object
        config= cls(
            ttt=TTTSpecConfig(**config["generators"]["ttt"]),
        )
        return config
    