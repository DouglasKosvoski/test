import os
from pathlib import Path
from typing import List


def list_files_in_directory(directory_path: str) -> List[str]:
    """
    Return file names (non-recursive) inside the given directory.

    Raises:
        FileNotFoundError: if the directory does not exist.
        NotADirectoryError: if the path exists but is not a directory.
    """
    path = Path(directory_path)

    if not path.exists():
        raise FileNotFoundError(f"Directory '{directory_path}' does not exist")

    if not path.is_dir():
        raise NotADirectoryError(f"Path '{directory_path}' is not a directory")

    return [entry.name for entry in os.scandir(path) if entry.is_file()]


def list_json_files_in_directory(directory_path: str) -> List[str]:
    """
    Return all JSON file names in the given directory.
    """
    return [
        name for name in list_files_in_directory(directory_path)
        if name.lower().endswith(".json")
    ]
