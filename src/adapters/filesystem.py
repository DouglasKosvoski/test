import os
import json
from pathlib import Path
from typing import List
from typing import Any


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
    """Return all JSON file names in the given directory."""
    return [
        name for name in list_files_in_directory(directory_path)
        if name.lower().endswith(".json")
    ]


def read_json_from_file(file_path: str | Path) -> Any:
    """
    Read and parse a JSON file.

    Raises:
        FileNotFoundError: if the file does not exist.
        json.JSONDecodeError: if the file content is not valid JSON.
    """
    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(f"File '{file_path}' does not exist")

    with path.open("r", encoding="utf-8") as file:
        try:
            return json.load(file)
        except json.JSONDecodeError as exc:
            raise json.JSONDecodeError(
                f"Invalid JSON in '{file_path}': {exc.msg}",
                exc.doc,
                exc.pos,
            ) from exc


def write_json_to_file(file_path: str | Path, data: Any) -> None:
    """Write JSON data to a file, ensuring the directory exists."""
    path = Path(file_path)

    if not path.parent.exists():
        os.makedirs(path.parent, exist_ok=True)

    # Optional: atomic write to avoid corrupted files
    temp_path = path.with_suffix(path.suffix + ".tmp")

    with temp_path.open("w", encoding="utf-8") as file:
        json.dump(data, file, indent=2, ensure_ascii=False)

    temp_path.replace(path)
