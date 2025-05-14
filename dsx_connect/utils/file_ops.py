import asyncio
import hashlib
import io
import logging
import pathlib
import re
import shutil
import os

import aiofiles
from pathlib import Path


def calculate_sha256_from_bytes(data):
    sha256_hash = hashlib.sha256(data.encode('utf-8'))
    return sha256_hash.hexdigest()


def calculate_sha256_from_bytesio(file_obj: io.BytesIO, chunk_size=8192):
    sha256_hash = hashlib.sha256()
    # Read the file in chunks so it can handle big files as well
    for byte_block in iter(lambda: file_obj.read(chunk_size), b""):
        sha256_hash.update(byte_block)

    return sha256_hash.hexdigest()


def calculate_sha256(filename, chunk_size=8192):
    sha256_hash = hashlib.sha256()
    with open(filename, 'rb') as f:
        for chunk in iter(lambda: f.read(chunk_size), b''):
            sha256_hash.update(chunk)
    return sha256_hash.hexdigest()


def copy_file(source_file, dest_file):
    source_path = Path(source_file).resolve()
    destination_path = Path(dest_file).resolve()
    pathlib.Path(destination_path.parent).mkdir(parents=True, exist_ok=True)
    shutil.copy2(source_path, dest_file)


def copy_files_recursively(source_dir, destination_dir, file_exclusions=None, folder_exclusions=None):
    """
    Args:
        source_dir (str): The path to the source directory.
        destination_dir (str): The path to the destination directory.
        file_exclusions (list, optional): A list of filenames to exclude from copying. Defaults to None.
        folder_exclusions (list, optional): A list of folder names to exclude from copying. Defaults to None.

    """
    source_path = Path(source_dir).resolve()
    destination_path = Path(destination_dir).resolve()

    for item_path in source_path.rglob('*'):
        if item_path.is_file():
            if str(item_path.name) in file_exclusions:
                continue
            relative_path = item_path.relative_to(source_path)
            if folder_exclusions and str(relative_path.parts[0]) in folder_exclusions:
                continue
            destination_file = destination_path / relative_path
            destination_file.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(item_path, destination_file)

async def read_file_async(filename, chunk_size=-1) -> io.BytesIO:
    """
    Reads file using aiofiles, if chunk file_sizes specified, will break up reading file into chunks
    """
    async with aiofiles.open(filename, mode='rb') as f:
        byte_io = io.BytesIO()
        if chunk_size == -1:
            try:
                content = await f.read()
                byte_io.write(content)
            except UnicodeDecodeError as e:
                logging.error(f'Could not read file: {filename} Unicode issue {e}')
        else:
            content = b''
            while True:
                chunk = await f.read(chunk_size)
                if not chunk:
                    break  # End of file
                byte_io.write(chunk)
        byte_io.seek(0)
        return byte_io


def read_file(filepath: pathlib.Path, chunk_size=-1) -> io.BytesIO:
    with filepath.open(mode='rb') as f:
        byte_io = io.BytesIO()
        if chunk_size == -1:
            try:
                content = f.read()
                byte_io.write(content)
            except UnicodeDecodeError as e:
                logging.error(f'Could not read file: {f} Unicode issue {e}')
        else:
            content = b''
            while True:
                chunk = f.read(chunk_size)
                if not chunk:
                    break  # End of file
                byte_io.write(chunk)
        byte_io.seek(0)
    return byte_io

def validate_filepath(path: Path):
    """
    Check for existence of a file path, and if it does not exist, throws a ValueError highlighting which part of the
    file path fails.
    Args:
        path: a file path

    Returns: True if exists, else a ValueError exception

    """
    if path.exists():
        return True
    # something in this path ain't right, let's figure out what...
    # Loop through each part of the folder name
    test_path = Path('')
    for part in path.parts:
        if part == '~':
            part = Path.home()
        parent_path = test_path
        test_path = test_path / part
        if not test_path.exists():
            folders = [str(folder.name) for folder in Path(parent_path).iterdir() if folder.is_dir()]
            raise ValueError(
                f'Filepath [{str(test_path)}] fails at [{part}]. The list of possible subdirectories under [{parent_path}] include: {folders}')

    return True


def get_filepaths(path: Path, recursive=True) -> list[Path]:
    """
    Given a folder/directory path, return all files paths within this folder, e.g.:
    get_filepaths(Path('c:/users/user/documents'), True)
    will return full file paths to all files contained in 'c:/users/user/documents' and files in subdirectories
    Args:
        path: a folder/directory as a pathlib.Path  if the path is just a file, the file_path for that file will be returned
        recursive:

    Returns: a list of pathlib.Path

    """
    if str(path).startswith('~'):
        path = path.expanduser()

    if not path.exists():
        return None

    files = []
    if path.is_file():  # the file_path specified is just a file, so just add it to the list of scanned items
        files.append(path)
        return files

    if recursive:
        files_and_folders = path.rglob("*")
    else:
        files_and_folders = path.glob("*")

    for full_name in files_and_folders:
        if not full_name.is_file():
            continue
        files.append(Path.absolute(full_name))

    return files


async def get_filepaths_async(path: Path, recursive=True):
    """
    Asynchronously iterate over file paths within the specified directory and yield each file path in turn.

    Args:
        path: a folder/directory as a pathlib.Path. If the path is just a file, the file_path for that file will be returned.
        recursive: if True, recurse into subdirectories.

    Yields:
        pathlib.Path: Each file path found in the directory.
    """
    # Expand user (~) if needed
    if str(path).startswith('~'):
        path = path.expanduser()

    # Return None if the path doesn't exist
    if not path.exists():
        return

    # If it's a file, yield the file path directly
    if path.is_file():
        yield path
        return

    # If recursive, use rglob; otherwise, use glob
    if recursive:
        files_and_folders = path.rglob("*")
    else:
        files_and_folders = path.glob("*")

    # Iterate over files asynchronously
    for full_name in files_and_folders:
        # Only yield file paths (skip directories)
        if full_name.is_file():
            yield full_name.absolute()
        # Simulate async processing
        await asyncio.sleep(0)  # Yield control back to the event loop

