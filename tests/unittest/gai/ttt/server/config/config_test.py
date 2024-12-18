import os
from gai.lib.config.config_utils import get_gai_config

def test_get_gai_config():
    here = os.path.dirname(__file__)
    config_path =  os.path.abspath(os.path.join(here,"..","..","..","..","..","..","src","gai","ttt","server","config","gai.yml"))
    config = get_gai_config(config_path)
    assert config["generators"]["ttt"]["default"]=="ttt-llamacpp-dolphin"
    
    
def test_get_default_server_config():
    
    # Get default config path
    here = os.path.dirname(__file__)
    config_path =  os.path.abspath(os.path.join(here,"..","..","..","..","..","..","src","gai","ttt","server","config","gai.yml"))
    
    # Load default config
    from gai.ttt.server.config.server_config_utils import get_llm_config
    llm_config = get_llm_config("ttt",config_path)
    print(llm_config)
    
    # assert
    assert llm_config.name=="ttt-llamacpp-dolphin"
    
def test_get_named_server_config():
    
    # Get default config path
    here = os.path.dirname(__file__)
    config_path =  os.path.abspath(os.path.join(here,"..","..","..","..","..","..","src","gai","ttt","server","config","gai.yml"))
    
    # Load default config
    from gai.ttt.server.config.server_config_utils import get_llm_config
    llm_config = get_llm_config("ttt-llamacpp-mistral7b",config_path)
    print(llm_config)
    
    # assert
    assert llm_config.name=="ttt-llamacpp-mistral7b"
    
