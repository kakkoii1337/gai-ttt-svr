import toml,os,subprocess
from gai.scripts._scripts_utils import _get_version

base_name="gai-ttt"

def _docker_run_ttt(component,version="latest"):
    if component != "gai-ttt":
        print("Wrong component found.")
        return
    cmd=f"""docker run -d \
        -e DEFAULT_GENERATOR="ttt-exllamav2-mistral7b" \
        -e SWAGGER_URL="/doc" \
        -e SELF_TEST="true" \
        --gpus all \
        -v ~/.gai:/app/.gai \
        -p 12031:12031 \
        --name {component} \
        --network gai-sandbox \
        kakkoii1337/{component}:{version}"""
    os.system(f"docker stop {component} && docker rm -f {component}")
    os.system(cmd)

def docker_run_ttt():
    here=os.path.dirname(__file__)
    pyproject_dir=os.path.join(here,'..')
    pyproject_path=os.path.join(pyproject_dir,'pyproject.toml')

    # Get the version from the pyproject.toml file
    version = _get_version(pyproject_path=pyproject_path)
    print(f"Running gai-ttt:{version}")

    # Exec the docker image
    _docker_run_ttt(component="gai-ttt",version=version)

if __name__ == "__main__":
    docker_run_ttt()