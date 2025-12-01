"""
Tests for adapter modules (filesystem, db).

These tests verify:
- File I/O operations
- JSON reading/writing
- Directory operations
- Error handling
"""

import pytest
import json
import os
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock, AsyncMock

from adapters.filesystem import (
    list_files_in_directory,
    list_json_files_in_directory,
    read_json_from_file,
    write_json_to_file,
)


class TestListFilesInDirectory:
    """Tests for list_files_in_directory function."""

    def test_list_files_in_empty_directory(self, temp_data_dirs):
        """Test listing files in empty directory returns empty list."""
        result = list_files_in_directory(str(temp_data_dirs["inbound"]))
        assert result == []

    def test_list_files_returns_file_names(self, temp_data_dirs):
        """Test listing files returns file names."""
        inbound = temp_data_dirs["inbound"]

        # Create some files
        (inbound / "file1.txt").touch()
        (inbound / "file2.json").touch()
        (inbound / "file3.py").touch()

        result = list_files_in_directory(str(inbound))

        assert len(result) == 3
        assert set(result) == {"file1.txt", "file2.json", "file3.py"}

    def test_list_files_excludes_directories(self, temp_data_dirs):
        """Test that directories are not included in the result."""
        inbound = temp_data_dirs["inbound"]

        # Create file and subdirectory
        (inbound / "file.txt").touch()
        (inbound / "subdir").mkdir()

        result = list_files_in_directory(str(inbound))

        assert result == ["file.txt"]

    def test_list_files_nonexistent_directory_raises(self):
        """Test that nonexistent directory raises FileNotFoundError."""
        with pytest.raises(FileNotFoundError):
            list_files_in_directory("/nonexistent/path")

    def test_list_files_not_a_directory_raises(self, temp_data_dirs):
        """Test that path to file raises NotADirectoryError."""
        inbound = temp_data_dirs["inbound"]
        file_path = inbound / "file.txt"
        file_path.touch()

        with pytest.raises(NotADirectoryError):
            list_files_in_directory(str(file_path))


class TestListJsonFilesInDirectory:
    """Tests for list_json_files_in_directory function."""

    def test_list_json_files_only(self, temp_data_dirs):
        """Test that only JSON files are returned."""
        inbound = temp_data_dirs["inbound"]

        # Create mixed files
        (inbound / "file1.json").touch()
        (inbound / "file2.JSON").touch()  # Uppercase extension
        (inbound / "file3.txt").touch()
        (inbound / "file4.py").touch()

        result = list_json_files_in_directory(str(inbound))

        assert len(result) == 2
        assert "file1.json" in result
        assert "file2.JSON" in result

    def test_list_json_files_empty_directory(self, temp_data_dirs):
        """Test empty directory returns empty list."""
        result = list_json_files_in_directory(str(temp_data_dirs["inbound"]))
        assert result == []

    def test_list_json_files_no_json_files(self, temp_data_dirs):
        """Test directory with no JSON files returns empty list."""
        inbound = temp_data_dirs["inbound"]
        (inbound / "file.txt").touch()
        (inbound / "file.py").touch()

        result = list_json_files_in_directory(str(inbound))
        assert result == []


class TestReadJsonFromFile:
    """Tests for read_json_from_file function."""

    def test_read_valid_json(self, temp_data_dirs):
        """Test reading valid JSON file."""
        inbound = temp_data_dirs["inbound"]
        filepath = inbound / "test.json"

        data = {"key": "value", "number": 42}
        with open(filepath, "w") as f:
            json.dump(data, f)

        result = read_json_from_file(str(filepath))

        assert result == data

    def test_read_json_with_path_object(self, temp_data_dirs):
        """Test reading using Path object."""
        inbound = temp_data_dirs["inbound"]
        filepath = inbound / "test.json"

        data = {"key": "value"}
        with open(filepath, "w") as f:
            json.dump(data, f)

        result = read_json_from_file(filepath)  # Path object

        assert result == data

    def test_read_nonexistent_file_raises(self):
        """Test reading nonexistent file raises FileNotFoundError."""
        with pytest.raises(FileNotFoundError):
            read_json_from_file("/nonexistent/file.json")

    def test_read_invalid_json_raises(self, temp_data_dirs):
        """Test reading invalid JSON raises JSONDecodeError."""
        inbound = temp_data_dirs["inbound"]
        filepath = inbound / "invalid.json"

        with open(filepath, "w") as f:
            f.write("{invalid json content")

        with pytest.raises(json.JSONDecodeError):
            read_json_from_file(str(filepath))

    def test_read_empty_file_raises(self, temp_data_dirs):
        """Test reading empty file raises JSONDecodeError."""
        inbound = temp_data_dirs["inbound"]
        filepath = inbound / "empty.json"
        filepath.touch()  # Create empty file

        with pytest.raises(json.JSONDecodeError):
            read_json_from_file(str(filepath))

    def test_read_json_with_unicode(self, temp_data_dirs):
        """Test reading JSON with unicode characters."""
        inbound = temp_data_dirs["inbound"]
        filepath = inbound / "unicode.json"

        data = {"text": "émojis 🔧 and ñ characters"}
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False)

        result = read_json_from_file(str(filepath))

        assert result["text"] == "émojis 🔧 and ñ characters"


class TestWriteJsonToFile:
    """Tests for write_json_to_file function."""

    def test_write_json_creates_file(self, temp_data_dirs):
        """Test writing JSON creates new file."""
        outbound = temp_data_dirs["outbound"]
        filepath = outbound / "new.json"

        data = {"key": "value"}
        write_json_to_file(str(filepath), data)

        assert filepath.exists()
        with open(filepath) as f:
            assert json.load(f) == data

    def test_write_json_overwrites_existing(self, temp_data_dirs):
        """Test writing JSON overwrites existing file."""
        outbound = temp_data_dirs["outbound"]
        filepath = outbound / "existing.json"

        # Write initial data
        with open(filepath, "w") as f:
            json.dump({"old": "data"}, f)

        # Overwrite
        new_data = {"new": "data"}
        write_json_to_file(str(filepath), new_data)

        with open(filepath) as f:
            assert json.load(f) == new_data

    def test_write_json_creates_parent_directories(self, temp_data_dirs):
        """Test writing JSON creates parent directories if needed."""
        root = temp_data_dirs["root"]
        filepath = root / "new" / "nested" / "dir" / "file.json"

        data = {"key": "value"}
        write_json_to_file(str(filepath), data)

        assert filepath.exists()

    def test_write_json_with_path_object(self, temp_data_dirs):
        """Test writing using Path object."""
        outbound = temp_data_dirs["outbound"]
        filepath = outbound / "pathobj.json"

        data = {"key": "value"}
        write_json_to_file(filepath, data)  # Path object

        assert filepath.exists()

    def test_write_non_serializable_raises(self, temp_data_dirs):
        """Test writing non-serializable data raises TypeError."""
        outbound = temp_data_dirs["outbound"]
        filepath = outbound / "error.json"

        # datetime objects are not JSON serializable by default
        from datetime import datetime

        data = {"date": datetime.now()}

        with pytest.raises(TypeError):
            write_json_to_file(str(filepath), data)

    def test_write_json_atomic_on_error(self, temp_data_dirs):
        """Test that atomic write doesn't corrupt existing file on error."""
        outbound = temp_data_dirs["outbound"]
        filepath = outbound / "protected.json"

        # Write initial valid data
        original = {"original": "data"}
        with open(filepath, "w") as f:
            json.dump(original, f)

        # Try to write non-serializable data
        from datetime import datetime

        try:
            write_json_to_file(str(filepath), {"date": datetime.now()})
        except TypeError:
            pass

        # Original file should be unchanged
        with open(filepath) as f:
            assert json.load(f) == original

    def test_write_json_with_unicode(self, temp_data_dirs):
        """Test writing JSON with unicode preserves characters."""
        outbound = temp_data_dirs["outbound"]
        filepath = outbound / "unicode.json"

        data = {"text": "émojis 🔧 and ñ characters"}
        write_json_to_file(str(filepath), data)

        with open(filepath, encoding="utf-8") as f:
            result = json.load(f)

        assert result["text"] == "émojis 🔧 and ñ characters"

    def test_write_json_formatted_with_indent(self, temp_data_dirs):
        """Test that JSON is written with indentation."""
        outbound = temp_data_dirs["outbound"]
        filepath = outbound / "formatted.json"

        data = {"key": "value", "nested": {"a": 1, "b": 2}}
        write_json_to_file(str(filepath), data)

        with open(filepath) as f:
            content = f.read()

        # Should be formatted (contain newlines and spaces)
        assert "\n" in content
        assert "  " in content  # Indentation


class TestDatabaseAdapter:
    """Tests for database adapter module."""

    @pytest.mark.asyncio
    async def test_get_connection_with_mongodb(self):
        """Test get_connection returns database for mongodb driver."""
        from adapters.db import get_connection

        with patch.dict(os.environ, {"DATABASE_DRIVER": "mongodb"}):
            with patch("adapters.db.get_mongodb_connection_with_retry", new_callable=AsyncMock) as mock:
                mock_db = MagicMock()
                mock.return_value = mock_db

                result = await get_connection()

                assert result == mock_db
                mock.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_connection_unsupported_driver_raises(self):
        """Test get_connection raises for unsupported driver."""
        from adapters.db import get_connection

        with patch.dict(os.environ, {"DATABASE_DRIVER": "postgresql"}):
            with pytest.raises(ValueError) as exc_info:
                await get_connection()

            assert "Unsupported database driver" in str(exc_info.value)

    def test_get_collection(self):
        """Test get_collection returns collection from database."""
        from adapters.db import get_collection

        mock_db = MagicMock()
        mock_collection = MagicMock()
        mock_db.__getitem__ = MagicMock(return_value=mock_collection)

        result = get_collection(mock_db, "test_collection")

        mock_db.__getitem__.assert_called_with("test_collection")
        assert result == mock_collection

    def test_get_collection_none_database_raises(self):
        """Test get_collection raises for None database."""
        from adapters.db import get_collection

        with pytest.raises(ValueError):
            get_collection(None, "collection")

    def test_get_collection_none_collection_name_raises(self):
        """Test get_collection raises for None collection name."""
        from adapters.db import get_collection

        mock_db = MagicMock()

        with pytest.raises(ValueError):
            get_collection(mock_db, None)


class TestFileSystemEdgeCases:
    """Edge case tests for filesystem operations."""

    def test_read_json_with_bom_raises_error(self, temp_data_dirs):
        """Test that JSON file with BOM marker raises JSONDecodeError.

        Note: Python's json module doesn't handle BOM when using utf-8 encoding.
        This test documents the current behavior - files with BOM should be
        created without BOM or the adapter should be enhanced to handle it.
        """
        inbound = temp_data_dirs["inbound"]
        filepath = inbound / "bom.json"

        # Write with BOM
        data = {"key": "value"}
        with open(filepath, "w", encoding="utf-8-sig") as f:
            json.dump(data, f)

        # Current implementation raises error for BOM files
        with pytest.raises(json.JSONDecodeError):
            read_json_from_file(str(filepath))

    def test_write_json_large_file(self, temp_data_dirs):
        """Test writing large JSON file."""
        outbound = temp_data_dirs["outbound"]
        filepath = outbound / "large.json"

        # Create large data (list of 10000 items)
        data = {"items": [{"id": i, "name": f"Item {i}"} for i in range(10000)]}

        write_json_to_file(str(filepath), data)

        with open(filepath) as f:
            result = json.load(f)

        assert len(result["items"]) == 10000

    def test_list_files_with_symlinks(self, temp_data_dirs):
        """Test listing files handles symlinks."""
        inbound = temp_data_dirs["inbound"]

        # Create a real file
        real_file = inbound / "real.json"
        real_file.touch()

        # Create symlink (may fail on some systems)
        try:
            link_file = inbound / "link.json"
            os.symlink(real_file, link_file)
        except OSError:
            pytest.skip("Symlinks not supported")

        result = list_files_in_directory(str(inbound))

        # Should include both real file and symlink
        assert len(result) == 2

    def test_write_json_special_characters_in_path(self, temp_data_dirs):
        """Test writing to path with special characters."""
        root = temp_data_dirs["root"]

        # Create directory with spaces and special chars
        special_dir = root / "my folder (1)"
        special_dir.mkdir()
        filepath = special_dir / "file.json"

        data = {"key": "value"}
        write_json_to_file(str(filepath), data)

        assert filepath.exists()
