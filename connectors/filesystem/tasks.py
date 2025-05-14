"""
Use invoke to run this script.
pip install invoke
invoke <task>

ex: invoke release
"""
import pathlib
import re
import os
import shutil
from invoke import task, run
from version import CONNECTOR_VERSION

name = 'filesystem-connector'
version = CONNECTOR_VERSION.strip()
build_dir = "dist"
export_folder = os.path.join(build_dir, f"{name}-{version}")
project_root_dir = str(pathlib.Path(__file__).resolve().parent.parent.parent)
repo_uname = "logangilbert"

@task
def bump(c):
    """Increment the build (patch) version in version.py."""
    filename = "version.py"
    with open(filename, "r") as f:
        content = f.read()

    pattern = r'(VERSION\s*=\s*["\'])(\d+)\.(\d+)\.(\d+)(["\'])'
    match = re.search(pattern, content)
    if not match:
        print("Version string not found in version.py")
        return

    major, minor, patch = int(match.group(2)), int(match.group(3)), int(match.group(4))
    new_patch = patch + 1
    new_version = f"{major}.{minor}.{new_patch}"
    new_line = f'{match.group(1)}{new_version}{match.group(5)}'
    new_content = re.sub(pattern, new_line, content)

    with open(filename, "w") as f:
        f.write(new_content)

    global version, export_folder
    version = new_version
    export_folder = os.path.join(build_dir, f"{name}-{version}")
    print(f"Bumped version to {new_version}")
    print(f"Export folder changed to {export_folder}")

@task
def clean(c):
    """Remove existing distribution folder and zip."""
    zip_file = f"{export_folder}.zip"
    print(f"Cleaning release folder: {export_folder} and {zip_file}...")
    if os.path.exists(export_folder):
        shutil.rmtree(export_folder)
    if os.path.exists(zip_file):
        os.remove(zip_file)

@task(pre=[clean])
def prepare(c):
    """Prepare distribution folder with necessary files."""
    print(f"Preparing release files for version {version}...")
    c.run(f"mkdir -p {export_folder}/connectors/filesystem")
    c.run(f"mkdir -p {export_folder}/dsx_connect/models")
    c.run(f"mkdir -p {export_folder}/dsx_connect/utils")

    # Copy connectors
    c.run(f"rsync -av --exclude '__pycache__' {project_root_dir}/connectors/filesystem/ {export_folder}/connectors/filesystem/ --exclude 'deploy' --exclude 'dist' --exclude 'tasks.py'")
    c.run(f"rsync -av --exclude '__pycache__' {project_root_dir}/connectors/framework/ {export_folder}/connectors/framework/")

    # Copy dsx_connect/models
    c.run(f"rsync -av --exclude '__pycache__' {project_root_dir}/dsx_connect/models/ {export_folder}/dsx_connect/models/")

    # Copy dsx_connect/utils
    c.run(f"rsync -av --exclude '__pycache__' {project_root_dir}/dsx_connect/utils/ {export_folder}/dsx_connect/utils/")

    # Copy top-level __init__.py
    # c.run(f"touch {export_folder}/__init__.py")
    c.run(f"touch {export_folder}/connectors/__init__.py")
    c.run(f"touch {export_folder}/dsx_connect/__init__.py")

    # Copy start.py to root folder
    c.run(f"mv {project_root_dir}/connectors/filesystem/start.py {export_folder}")

    #
    # c.run(f"mv {project_root_dir}/connectors/filesystem/README.md {export_folder}/README.md")

    # Generate requirements.txt
    c.run(f"pipreqs {export_folder} --force --savepath {export_folder}/requirements.txt")

    # move Dockerfile and docker-compose to topmost directory
    c.run(f"rsync -av {project_root_dir}/connectors/filesystem/deploy/ {export_folder}")

#     # Generate Dockerfile
#     with open(f"{export_folder}/Dockerfile", "w") as f:
#         f.write('''FROM python:3.12-slim
#
# # Create a non-root user
# RUN useradd -m appuser
#
# WORKDIR /app
#
# COPY requirements.txt .
# RUN pip install --no-cache-dir -r requirements.txt
#
# RUN mkdir quarantine
# RUN mkdir scan_folder
#
# COPY connectors/ connectors/
# COPY dsx_connect/ dsx_connect/
# COPY utils/ utils/
# COPY start.py .
#
# ENV PYTHONPATH=/app
#
# USER appuser
#
# # Command is set in docker-compose.yaml
# ''')
#
#     # Generate docker-compose.yaml
#     with open(f"{export_folder}/docker-compose.yaml", "w") as f:
#         f.write('''services:
#   filesystem_connector:
#     build:
#       context: .
#       dockerfile: Dockerfile
#     ports:
#       - "8590:8590"
#     volumes:
#       - /Users/logangilbert/Documents/SAMPLES/PDF:/app/scan_folder  # this directory should have been created in the Dockerfile
#     environment:
#       - PYTHONUNBUFFERED=1
#       - DSXCONNECTOR_CONNECTOR_URL=http://filesystem-connector-api:8590 # see aliases below
#       - DSXCONNECTOR_DSX_CONNECT_URL=http://dsx-connect-api:8586 # note, this works if running on the same internal network on Docker as the dsx_connect_core...
#       - DSXCONNECTOR_LOCATION=/app/scan_folder
#       - LOG_LEVEL=debug
#       - DSXCONNECTOR_ITEM_ACTION=nothing
#       - DSXCONNECTOR_ITEM_ACTION_MOVE_DIR=/app/quarantine # this directory should have been created in the Dockerfile
#       - DSXCONNECTOR_RECURSIVE=true
#     networks:
#       dsx-network:
#         aliases:
#           - filesystem-connector-api  # this is how dsx-connect will communicate with this on the network
#     command:
#       python connectors/filesystem/filesystem_connector.py
#
# # The following assumes an already created docker network like this:
# # docker network create dsx-connect-network --driver bridge
# networks:
#     dsx-network:
#       external: true
#       name: dsx-connect-network  # change this to an existing docker network
# ''')

@task(pre=[prepare])
def build(c):
    """Build Docker image from distribution."""
    image_tag = f"{name}:{version}"
    result = c.run(f"docker images -q {image_tag}", hide=True)
    if result.stdout.strip():
        print(f"Image {image_tag} already exists. Skipping build.")
    else:
        print(f"Building docker image {image_tag}...")
        c.run(f"docker build -t {image_tag} {export_folder}")

@task(pre=[build])
def push(c):
    """Push Docker image to Docker Hub."""
    print("Pushing image to Docker Hub...")
    c.run(f"docker tag {name}:{version} {repo_uname}/{name}:{version}")
    c.run(f"docker push {repo_uname}/{name}:{version}")

@task
def run(c):
    """Run Docker image locally."""
    print(f"Running image {name}:{version}")
    c.run(f"docker run -p 0:0 {name}:{version}")

@task(pre=[prepare])
def generate_requirements(c):
    """Generate requirements.txt using pipreqs."""
    c.run(f"pipreqs {export_folder} --force --savepath {export_folder}/requirements.txt")

@task
def release(c):
    """Perform full release cycle."""
    bump(c)
    clean(c)
    prepare(c)
    build(c)
    push(c)