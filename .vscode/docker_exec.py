import toml,os,subprocess

base_name="gai-ttt"

## Update version in pyproject.toml
def __update_version(pyproject_path):
    with open(pyproject_path, "r+") as f:
        data = toml.load(f)

        # Extract and update the version number
        version_parts = data["tool"]["poetry"]["version"].split(".")
        version_parts[-1] = str(int(version_parts[-1]) + 1)  # Increment the patch version
        data["tool"]["poetry"]["version"] = ".".join(version_parts)

        # Write the updated data back to pyproject.toml
        f.seek(0)
        f.write(toml.dumps(data))
        f.truncate()  # Ensure file is truncated if new data is shorter

        return data["tool"]["poetry"]["version"]

def _docker_exec_ttt(component):
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
        kakkoii1337/{component}:latest"""
    os.system(f"docker stop {component} && docker rm -f {component}")
    os.system(cmd)

def main():
    here=os.path.dirname(__file__)
    pyproject_dir=os.path.join(here,'..')
    dockerfile_dir=pyproject_dir
    pyproject_path=os.path.join(pyproject_dir,'pyproject.toml')

    # Get the version from the pyproject.toml file
    version = __update_version(pyproject_path=pyproject_path)
    print(f"Building docker image with version: {version}")

    # Exec the docker image
    _docker_exec_ttt(component="gai-ttt")

if __name__ == "__main__":
    main()