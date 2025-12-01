import json
from pathlib import Path
from typing import Any


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
    """
    Write JSON data to a file, ensuring the directory exists.

    Raises:
        NotADirectoryError: if the target directory does not exist.
    """
    path = Path(file_path)

    if not path.parent.exists():
        raise NotADirectoryError(
            f"Directory '{path.parent}' does not exist for output file"
        )

    # Optional: atomic write to avoid corrupted files
    temp_path = path.with_suffix(path.suffix + ".tmp")

    with temp_path.open("w", encoding="utf-8") as file:
        json.dump(data, file, indent=4, ensure_ascii=False)

    temp_path.replace(path)
