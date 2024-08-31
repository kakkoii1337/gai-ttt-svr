import toml,os,subprocess

repo_name="kakkoii1337/"
base_name="gai-ttt-exllama-devcontainer"

## Update version in pyproject.toml
def __get_version(pyproject_path):
    with open(pyproject_path, "r+") as f:
        data = toml.load(f)
    return data["tool"]["poetry"]["version"]

def main():
    here=os.path.dirname(__file__)
    pyproject_path=os.path.join(here,'..','pyproject.toml')

    # Push version from the pyproject.toml file
    version = __get_version(pyproject_path=pyproject_path)
    os.system(f"docker tag {repo_name}{base_name}:{version} {repo_name}{base_name}:{version}")
    os.system(f"docker push {repo_name}{base_name}:{version}")
    print(f"Pushed image {repo_name}{base_name}:{version}")

    # Push latest
    version = "latest"
    os.system(f"docker tag {base_name}:{version} {repo_name}{base_name}:{version}")
    os.system(f"docker push {repo_name}{base_name}:{version}")
    print(f"Pushed image {repo_name}{base_name}:{version}")

if __name__ == "__main__":
    main()
