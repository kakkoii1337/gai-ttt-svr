import os
from gai.lib.config.config_utils import get_gai_config
def test_get_gai_config():
    here = os.path.dirname(__file__)
    config_path =  os.path.abspath(os.path.join(here,"..","..","..","..","..","..","src","gai","ttt","server","config","gai.yml"))
    config = get_gai_config(config_path)
    assert config["generators"]["ttt"]["default"]=="ttt-llamacpp-dolphin"
    
    
def test_get_server_config():
    
    # Load config
    here = os.path.dirname(__file__)
    config_path =  os.path.abspath(os.path.join(here,"..","..","..","..","..","..","src","gai","ttt","server","config","gai.yml"))
    config = get_gai_config(config_path)

    # Parse config
    from gai.ttt.server.config.ttt_config import ServerConfig
    server_config = ServerConfig.from_config(config)
    default = server_config.ttt.default
    
    # assert
    assert server_config.ttt.default=="ttt-llamacpp-dolphin"
    assert server_config.ttt.configs[default].type=="ttt"
    assert server_config.ttt.configs[default].module.class_=="GaiLlamaCpp"
    
# This is to test the initial creation of the config in config file when read is unable to find the config specs
def test_update_config():
    
    # step 1: Copy sample.yml to /tmp
    import shutil
    import tempfile
    here = os.path.dirname(__file__)
    sample_path =  os.path.abspath(os.path.join(here,"sample.yml"))
    tmpdir = "/tmp"
    shutil.copy(sample_path, tmpdir)
    
    # step 2: Read the config
    from gai.lib.config.config_utils import get_gai_config
    config_path = os.path.join(tmpdir,"sample.yml")
    config = get_gai_config(config_path)
    if not config.get("generators"):
        config["generators"] = {}
    if not config["generators"].get("ttt"):
        config["generators"]["ttt"] = {}
        # Load default
        default_path = os.path.abspath(os.path.join(here,"..","..","..","..","..","..","src","gai","ttt","server","config","gai.yml"))
        default_config = get_gai_config(default_path)
        config["generators"]["ttt"]=default_config["generators"]["ttt"]
        
    # step 3: Save the config
    import yaml
    with open(config_path, 'w') as f:
        yaml.dump(config, f, sort_keys=False)
    
    
    