import toml,os,subprocess
from gai.scripts._scripts_utils import _get_version,_get_project_name

base_name="gai-ttt-svr-exllamav2"

def _docker_run_ttt(project_name,version="latest"):
    if project_name != base_name:
        print("Wrong project_name found.")
        return
    use_network = ""

    if os.environ.get("USE_SANDBOX_NETWORK") == "true":
        print("Running in sandbox network")
        use_network = "--network gai-sandbox"
    cmd=f"""docker run -d \
        -e DEFAULT_GENERATOR="ttt-exllamav2-mistral7b" \
        -e SWAGGER_URL="/doc" \
        -e SELF_TEST="true" \
        --gpus all \
        -v ~/.gai:/root/.gai \
        -p 12031:12031 \
        --name {project_name} \
        {use_network} \
        kakkoii1337/{project_name}:{version}"""
    os.system(f"docker stop {project_name} && docker rm -f {project_name}")
    os.system(cmd)

def docker_run_ttt():
    here=os.path.dirname(__file__)
    pyproject_dir=os.path.join(here,'..')
    pyproject_path=os.path.join(pyproject_dir,'pyproject.toml')

    # Get the version from the pyproject.toml file
    version = _get_version(pyproject_path=pyproject_path)
    print(f"Running gai-ttt:{version}")

    # Exec the docker image
    project_name = _get_project_name(pyproject_path=pyproject_path)
    _docker_run_ttt(project_name=project_name,version=version)

if __name__ == "__main__":
    docker_run_ttt()