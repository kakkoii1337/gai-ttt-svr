import toml,os,subprocess

repo_name="kakkoii1337/"
base_name="gai-ttt-exllama-devcontainer"

## Update version in pyproject.toml
def __update_version(pyproject_path):
    with open(pyproject_path, "r+") as f:
        data = toml.load(f)

        # Extract and update the version number
        version=data["tool"]["poetry"]["version"]
        version_parts = version.split(".")
        version_parts[-1] = str(int(version_parts[-1]) + 1)  # Increment the patch version
        version = ".".join(version_parts)

        # Write the updated data back to pyproject.toml
        f.seek(0)
        f.write(toml.dumps(data))
        f.truncate()  # Ensure file is truncated if new data is shorter

        return version


def main():
    here=os.path.dirname(__file__)
    pyproject_dir=os.path.join(here,'..')
    pyproject_path=os.path.join(pyproject_dir,'pyproject.toml')
    dockerfile_dir=os.path.abspath(os.path.join(pyproject_dir,'.devcontainer'))
    context_dir = pyproject_dir

    # Get the version from the pyproject.toml file
    version = __update_version(pyproject_path=pyproject_path)
    print(f"Building docker image with version: {version}")

    # Build the docker image
    os.system(f"docker build -t {repo_name}{base_name}:{version} -f {dockerfile_dir}/Dockerfile.devcontainer {context_dir}")
    os.system(f"docker tag {repo_name}{base_name}:{version} {repo_name}{base_name}:latest")

if __name__ == "__main__":
    main()