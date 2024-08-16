import subprocess
import os,sys
this_dir=os.path.dirname(os.path.realpath(__file__))
from os.path import dirname, abspath
from rich.console import Console
console=Console()
import toml

def _cmd(cmd):
    try:
        subprocess.run(cmd, shell=True, check=True)
    except subprocess.CalledProcessError as e:
        print("Error: ", e)
        return

def _get_version(pyproject_path):
    data = toml.load(pyproject_path)
    # Extract the version from the [tool.poetry] section
    version = data['tool']['poetry']['version']
    return version

# PACKAGE

def _publish_package(env, proj_path):

    ## Update version in pyproject.toml
    def __update_version():
        # Load the pyproject.toml file
        with open(os.path.join(proj_path,"pyproject.toml"), "r+") as f:
            data = toml.load(f)

            # Extract and update the version number
            version_parts = data["tool"]["poetry"]["version"].split(".")
            version_parts[-1] = str(int(version_parts[-1]) + 1)  # Increment the patch version
            data["tool"]["poetry"]["version"] = ".".join(version_parts)

            # Write the updated data back to pyproject.toml
            f.seek(0)
            f.write(toml.dumps(data))
            f.truncate()  # Ensure file is truncated if new data is shorter

    def __remove_dist_dir():
        # Remove the dist directory
        subprocess.run(["rm", "-rf", "dist"], check=True)

    def __build_package():
        # Running 'poetry build' to create package distributions
        os.system(f"cd {proj_path} && poetry build")

    def __publish_package(env, proj_path):
        os.system(f"eval \"$(conda shell.bash hook)\" && conda activate {env} && cd {proj_path} && TWINE_USERNAME=__token__ twine upload dist/*")

    print("Updating version in pyproject.toml")
    __update_version()

    print("Building the package")
    __remove_dist_dir()
    __build_package()

    print("Publishing the package to PyPI")
    try:
        __publish_package(env, proj_path)
        print("Package published successfully.")
    except subprocess.CalledProcessError:
        print("Failed to publish the package.", file=sys.stderr)
        sys.exit(1)
   

# DOCKER

def _docker_container_exists(container_name):
    try:
        # Execute docker ps to list all containers
        result = subprocess.run(
            ["docker", "ps", "-a", "--format", "{{.Names}}"],
            capture_output=True,
            text=True,
            check=True
        )
        # Check if the specified container name is in the output
        return container_name in result.stdout.split()
    except subprocess.CalledProcessError:
        # If there is an error executing docker ps, assume the container does not exist
        return False
    
def _docker_image_exists(image_name):
    try:
        # Execute docker images to list all images
        result = subprocess.run(
            ["docker", "images", "--format", "{{.Repository}}:{{.Tag}}"],
            capture_output=True,
            text=True,
            check=True
        )
        # Check if the specified image name is in the output
        return image_name in result.stdout.split('\n')
    except subprocess.CalledProcessError:
        # If there is an error executing docker images, assume the image does not exist
        return False        
    
def _docker_build(component_name,
                version,
                dockercontext_path, 
                dockerfile_path=None, 
                no_cache=False):
    
    repo_name = "kakkoii1337"

    if not dockerfile_path:
        dockerfile_path = f"{dockercontext_path}/Dockerfile"

    # build        
    console.print(f"""[yellow]**Build {component_name}:{version}**[/]""")
    if no_cache:
        console.print(f"""[blue]--no-cache[/]""")
    console.print(f"""[white]dockerfile: {dockerfile_path}[/]""")
    console.print(f"""[white]context: {dockercontext_path}[/]""")
    if _docker_image_exists(f"{component_name}:{version}"):
        console.print(f"""[white]Removing existing {component_name}:{version}[/]""")
        _cmd(f"""docker rmi -f {component_name}:{version}""")
    cmd=f"""docker buildx build """ + ("""--no-cache""" if no_cache else "") + f""" \
        --progress=plain \
        -f {dockerfile_path} \
        -t {component_name}:{version} \
        {dockercontext_path}"""
    _cmd(cmd)

    # remove dangling before tagging
    if (_docker_container_exists(component_name)):
        _docker_stop(component_name)
        if _docker_image_exists(f"{component_name}:latest"):
            _cmd(f"docker rmi {component_name}:latest")
        if _docker_image_exists(f"{repo_name}/{component_name}:latest"):
            _cmd(f"docker rmi {repo_name}/{component_name}:latest")
    _cmd(f"docker tag {component_name}:{version} {component_name}:latest")
    _cmd(f"docker tag {component_name}:{version} {repo_name}/{component_name}:latest")
    
    console.print(f"""[green bold]Build {component_name}:{version} Done[/]""")

def _docker_stop(component_name):
    if _docker_container_exists(component_name):
        console.print(f"""[yellow]**Stopping {component_name}**[/]""")
        _cmd(f"""docker stop {component_name}""")
        _cmd(f"""docker rm -f {component_name}""")
        console.print(f"""[bold green]**Docker container {component_name} stopped.[/]""")

def _docker_logs(component_name):
    _cmd(f"""docker logs {component_name}""")

def _docker_idle(component_name):
    _cmd(f"""docker run -d --name {component_name} {component_name}:latest 
         bash -c "while true; do sleep 1000; done"
         """)

def _docker_ssh(component_name):
    _cmd(f"docker exec -it {component_name} bash")

def _docker_pull(component_name, version=None):
    repo="kakkoii1337"
    _cmd(f"docker pull {repo}/{component_name}:latest")
    if version:
        _cmd(f"docker pull {repo}/{component_name}:{version}")

def _docker_push(component_name, version):
    repo="kakkoii1337"

    local_image_name=f"{component_name}:{version}"    
    repo_image_name=f"{repo}/{local_image_name}"
    console.print(f"""[yellow]**Pushing {repo_image_name}**[/]""")
    _cmd(f"docker tag {local_image_name} {repo_image_name}")
    _cmd(f"docker push {repo_image_name}")
    console.print(f"""[green bold]Pushed {repo_image_name}[/]""")

    version = "latest"
    local_image_name=f"{component_name}:{version}"    
    repo_image_name=f"{repo}/{local_image_name}"
    console.print(f"""[yellow]**Pushing {repo_image_name}**[/]""")
    _cmd(f"docker tag {local_image_name} {repo_image_name}")
    _cmd(f"docker push {repo_image_name}")
    console.print(f"""[green bold]Pushed {repo_image_name}[/]""")

def _docker_rmi(component_name,version=None):
    _cmd(f"docker rmi {component_name}:latest")
    if version:
        _cmd(f"docker rmi {component_name}:{version}")
