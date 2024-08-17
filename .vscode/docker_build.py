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


def main():
    here=os.path.dirname(__file__)
    pyproject_dir=os.path.join(here,'..')
    dockerfile_dir=pyproject_dir
    pyproject_path=os.path.join(pyproject_dir,'pyproject.toml')

    # Get the version from the pyproject.toml file
    version = __update_version(pyproject_path=pyproject_path)
    print(f"Building docker image with version: {version}")

    # Build the docker image
    os.system(f"docker build -t {base_name}:{version} {dockerfile_dir}")
    os.system(f"docker tag {base_name}:{version} {base_name}:latest")

if __name__ == "__main__":
    main()