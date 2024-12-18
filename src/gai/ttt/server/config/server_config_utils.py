import os
from gai.ttt.server.config.pydantic.ttt_config import ServerConfig
from gai.lib.config.config_utils import get_gai_config, save_gai_config

def get_llm_config(config_type_or_name:str, file_path:str=None) -> ServerConfig:
    # Load from config file
    gai_config = get_gai_config(file_path)
    here = os.path.dirname(__file__)
    default_path = os.path.abspath(os.path.join(here,"..","config","gai.yml"))
    default_config = get_gai_config(default_path)
    
    # Create config file if not exists
    if not gai_config.get("generators"):
        gai_config["generators"] = {}
    if not gai_config["generators"].get("ttt"):
        gai_config["generators"]["ttt"] = {}

    # Create default server if not exists
    if not gai_config["generators"]["ttt"].get("default"):
        here = os.path.dirname(__file__)
        default_path = os.path.abspath(os.path.join(here,"..","config","gai.yml"))
        default_config = get_gai_config(default_path)
        gai_config["generators"]["ttt"]["default"] = default_config["generators"]["ttt"]["default"]
    
    # Create server configs if not exists
    def create_server_config(name):
        gai_config["generators"]["ttt"]["configs"][name]=default_config["generators"]["ttt"]["configs"][name]
        save_gai_config(gai_config)    
    for server_config in default_config["generators"]["ttt"]["configs"]:
        if not gai_config["generators"]["ttt"]["configs"].get(server_config):
            create_server_config(server_config)    
    
    # Override by environment variables
    if os.getenv("DEFAULT_GENERATOR"):
        gai_config["generators"]["ttt"]["default"] = os.environ["DEFAULT_GENERATOR"]
    default = gai_config["generators"]["ttt"]["default"]
    if os.getenv("MAX_SEQ_LEN"):
        gai_config["generators"]["ttt"]["configs"][default]["max_seq_len"] = int(os.environ["MAX_SEQ_LEN"])

    # Dynamically access the category attribute
    server_config = ServerConfig.from_config(gai_config)
    if config_type_or_name == "ttt":
        default = server_config.ttt.default
        return server_config.ttt.configs[default]
    return server_config.ttt.configs[config_type_or_name]
    