import os
from gai.ttt.server.config.ttt_config import ServerConfig

def get_gai_config(file_path:str=None) -> ServerConfig:
    from gai.lib.config.config_utils import get_gai_config, save_gai_config
    gai_config = get_gai_config(file_path)
    
    # Load from config file or create config file if not exists
    if not gai_config.get("generators"):
        gai_config["generators"] = {}
    if not gai_config["generators"].get("ttt"):
        gai_config["generators"]["ttt"] = {}
        # Load default
        here = os.path.dirname(__file__)
        default_path = os.path.abspath(os.path.join(here,"..","config","gai.yml"))
        default_config = get_gai_config(default_path)
        gai_config["generators"]["ttt"]=default_config["generators"]["ttt"]
        # Save default to config file without environment variables updates
        save_gai_config(gai_config)
    
    # Override by environment variables
    if os.getenv("DEFAULT_GENERATOR"):
        gai_config["generators"]["ttt"]["default"] = os.environ["DEFAULT_GENERATOR"]
    default = gai_config["generators"]["ttt"]["default"]
    if os.getenv("MAX_SEQ_LEN"):
        gai_config["generators"]["ttt"]["configs"][default]["max_seq_len"] = int(os.environ["MAX_SEQ_LEN"])

    # Return the final config
    server_config = ServerConfig.from_config(gai_config)
    return server_config

def save_gai_config(gai_config:dict, file_path:str=None):
    from gai.lib.config.config_utils import save_gai_config
    save_gai_config(gai_config, file_path)
    