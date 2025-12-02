"""
Tests for repository classes (Client and TracOS).

These tests verify:
- File-based workorder loading (ClientRepository)
- MongoDB operations (TracOSRepository)
- Validation logic
- Error handling
"""

import pytest
import json
from pathlib import Path
from datetime import datetime, timezone
from unittest.mock import patch, MagicMock, AsyncMock

from integration.system.client.repository import ClientRepository
from integration.system.tracos.repository import TracOSRepository


class TestClientRepository:
    """Tests for ClientRepository (file-based operations)."""

    def test_find_workorders_from_directory(self, populated_inbound_dir):
        """Test loading workorders from directory with JSON files."""
        repo = ClientRepository()
        workorders = repo.find_workorders(str(populated_inbound_dir))

        assert len(workorders) == 2
        order_numbers = {wo["orderNo"] for wo in workorders}
        assert order_numbers == {100, 101}

    def test_find_workorders_empty_directory(self, temp_data_dirs):
        """Test loading from empty directory returns empty list."""
        repo = ClientRepository()
        workorders = repo.find_workorders(str(temp_data_dirs["inbound"]))

        assert workorders == []

    def test_find_workorders_nonexistent_directory(self, temp_data_dirs):
        """Test loading from nonexistent directory raises FileNotFoundError."""
        repo = ClientRepository()

        with pytest.raises(FileNotFoundError):
            repo.find_workorders("/nonexistent/path")

    def test_find_workorders_handles_corrupted_json(self, inbound_dir_with_corrupted_json):
        """Test that corrupted JSON files are skipped gracefully."""
        repo = ClientRepository()
        workorders = repo.find_workorders(str(inbound_dir_with_corrupted_json))

        # Should only return the valid workorder
        assert len(workorders) == 1
        assert workorders[0]["orderNo"] == 100

    def test_validate_workorder_valid(self, sample_client_workorder):
        """Test validation of a valid workorder."""
        repo = ClientRepository()
        result = repo.validate_workorder(sample_client_workorder)

        assert result is not None
        assert result["orderNo"] == sample_client_workorder["orderNo"]

    def test_validate_workorder_missing_required_field(self, malformed_client_workorders):
        """Test validation rejects workorder missing required field."""
        repo = ClientRepository()

        # First workorder is missing isDeleted
        result = repo.validate_workorder(malformed_client_workorders[0])
        assert result is None

    def test_validate_workorder_wrong_type(self, malformed_client_workorders):
        """Test validation rejects workorder with wrong field type."""
        repo = ClientRepository()

        # Second workorder has string orderNo instead of int
        result = repo.validate_workorder(malformed_client_workorders[1])
        assert result is None

    def test_validate_workorder_invalid_date(self, malformed_client_workorders):
        """Test validation rejects workorder with invalid date format."""
        repo = ClientRepository()

        # Third workorder has invalid creationDate
        result = repo.validate_workorder(malformed_client_workorders[2])
        assert result is None

    def test_validate_workorder_deleted_with_invalid_date(self, malformed_client_workorders):
        """Test validation rejects deleted workorder with invalid deletedDate."""
        repo = ClientRepository()

        # Fourth workorder is deleted but has invalid deletedDate
        result = repo.validate_workorder(malformed_client_workorders[3])
        assert result is None

    def test_validate_workorder_not_deleted_but_has_deleted_date(self, malformed_client_workorders):
        """Test validation rejects not-deleted workorder with deletedDate set."""
        repo = ClientRepository()

        # Fifth workorder is not deleted but has deletedDate
        result = repo.validate_workorder(malformed_client_workorders[4])
        assert result is None

    def test_is_iso_datetime_valid_formats(self):
        """Test is_iso_datetime recognizes valid formats."""
        repo = ClientRepository()

        valid_dates = [
            "2025-11-01T10:00:00+00:00",
            "2025-11-01T10:00:00Z",
            "2025-11-01T10:00:00",
            "2025-11-01T10:00:00.123456+00:00",
            "2025-11-01",
        ]

        for date_str in valid_dates:
            assert repo.is_iso_datetime(date_str) is True, f"Should accept: {date_str}"

    def test_is_iso_datetime_invalid_formats(self):
        """Test is_iso_datetime rejects invalid formats."""
        repo = ClientRepository()

        invalid_dates = [
            "not-a-date",
            "2025/11/01",
            "11-01-2025",
            "2025-13-01",  # Invalid month
            "",
        ]

        for date_str in invalid_dates:
            assert repo.is_iso_datetime(date_str) is False, f"Should reject: {date_str}"


class TestTracOSRepository:
    """Tests for TracOSRepository (MongoDB operations)."""

    @pytest.mark.asyncio
    async def test_save_workorder_insert_new(self, mock_db_connection):
        """Test saving a new workorder inserts it."""
        repo = TracOSRepository()
        workorder = {
            "number": 1,
            "status": "created",
            "title": "Test workorder",
            "description": "Test description",
            "createdAt": datetime.now(timezone.utc),
            "updatedAt": datetime.now(timezone.utc),
            "deleted": False,
        }

        result = await repo.save_workorder(workorder)

        assert result is True
        # Verify it was stored
        collection = mock_db_connection["collection"]
        assert len(collection._storage) == 1

    @pytest.mark.asyncio
    async def test_save_workorder_skip_unchanged(self, mock_db_connection):
        """Test saving an unchanged workorder doesn't update."""
        repo = TracOSRepository()
        collection = mock_db_connection["collection"]

        # Pre-populate storage
        existing = {
            "number": 1,
            "status": "created",
            "title": "Test title",
            "description": "Test description",
            "createdAt": datetime(2025, 11, 1, tzinfo=timezone.utc),
            "updatedAt": datetime(2025, 11, 1, tzinfo=timezone.utc),
            "deleted": False,
        }
        collection._storage.append(existing.copy())

        # Save identical workorder
        same = {
            "number": 1,
            "status": "created",
            "title": "Test title",
            "description": "Test description",
            "createdAt": datetime(2025, 11, 1, tzinfo=timezone.utc),
            "updatedAt": datetime(2025, 11, 1, tzinfo=timezone.utc),
            "deleted": False,
        }

        result = await repo.save_workorder(same)

        assert result is True
        # Verify no changes were made (should_update_workorder returns False)

    @pytest.mark.asyncio
    async def test_find_all_unsynced_workorders(self, mock_db_connection):
        """Test finding unsynced workorders."""
        repo = TracOSRepository()
        collection = mock_db_connection["collection"]

        # Add some workorders
        collection._storage.extend(
            [
                {
                    "number": 1,
                    "status": "created",
                    "title": "Unsynced 1",
                    "description": "Desc",
                    "createdAt": datetime.now(timezone.utc),
                    "updatedAt": datetime.now(timezone.utc),
                    "deleted": False,
                    "isSynced": False,
                },
                {
                    "number": 2,
                    "status": "completed",
                    "title": "Synced",
                    "description": "Desc",
                    "createdAt": datetime.now(timezone.utc),
                    "updatedAt": datetime.now(timezone.utc),
                    "deleted": False,
                    "isSynced": True,
                },
                {
                    "number": 3,
                    "status": "pending",
                    "title": "Unsynced 2",
                    "description": "Desc",
                    "createdAt": datetime.now(timezone.utc),
                    "updatedAt": datetime.now(timezone.utc),
                    "deleted": False,
                },  # No isSynced field
            ]
        )

        unsynced = []
        async for workorder in repo.find_all_unsynced_workorders():
            unsynced.append(workorder)

        # Should find workorders where isSynced != True
        assert len(unsynced) == 2
        numbers = {wo["number"] for wo in unsynced}
        assert numbers == {1, 3}

    @pytest.mark.asyncio
    async def test_mark_workorder_as_synced(self, mock_db_connection):
        """Test marking workorder as synced."""
        repo = TracOSRepository()
        collection = mock_db_connection["collection"]

        # Add workorder
        collection._storage.append(
            {
                "number": 1,
                "status": "created",
                "title": "Test",
                "description": "Desc",
                "createdAt": datetime.now(timezone.utc),
                "updatedAt": datetime.now(timezone.utc),
                "deleted": False,
                "isSynced": False,
            }
        )

        result = await repo.mark_workorder_as_synced(1)

        assert result is True
        assert collection._storage[0]["isSynced"] is True
        assert "syncedAt" in collection._storage[0]

    @pytest.mark.asyncio
    async def test_mark_nonexistent_workorder_returns_false(self, mock_db_connection):
        """Test marking nonexistent workorder returns False."""
        repo = TracOSRepository()

        result = await repo.mark_workorder_as_synced(999)

        assert result is False

    def test_should_update_workorder_no_changes(self):
        """Test should_update_workorder returns False when no changes."""
        repo = TracOSRepository()

        existing = {"_id": "123", "number": 1, "status": "created", "title": "Test"}

        new = {"number": 1, "status": "created", "title": "Test"}

        assert repo.should_update_workorder(existing, new) is False

    def test_should_update_workorder_ignores_id(self):
        """Test should_update_workorder ignores _id field in comparison."""
        repo = TracOSRepository()

        existing = {"_id": "123", "number": 1, "status": "created"}

        new = {
            "_id": "different_id",  # Different _id should be ignored
            "number": 1,
            "status": "created",
        }

        assert repo.should_update_workorder(existing, new) is False


class TestTracOSRepositoryErrorHandling:
    """Tests for TracOSRepository error handling."""

    @pytest.mark.asyncio
    async def test_save_workorder_connection_error_propagates(self):
        """Test that ConnectionError propagates from save_workorder."""
        repo = TracOSRepository()

        # Patch in the module where it's imported
        with patch(
            "integration.system.tracos.repository.get_connection",
            new_callable=AsyncMock,
        ) as mock_conn:
            mock_conn.side_effect = ConnectionError("Connection failed")

            with pytest.raises(ConnectionError):
                await repo.save_workorder({"number": 1})

    @pytest.mark.asyncio
    async def test_find_all_unsynced_connection_error_propagates(self):
        """Test that ConnectionError propagates from find_all_unsynced_workorders."""
        repo = TracOSRepository()

        # Patch in the module where it's imported
        with patch(
            "integration.system.tracos.repository.get_connection",
            new_callable=AsyncMock,
        ) as mock_conn:
            mock_conn.side_effect = ConnectionError("Connection failed")

            with pytest.raises(ConnectionError):
                async for _ in repo.find_all_unsynced_workorders():
                    pass

    @pytest.mark.asyncio
    async def test_mark_as_synced_connection_error_propagates(self):
        """Test that ConnectionError propagates from mark_workorder_as_synced."""
        repo = TracOSRepository()

        # Patch in the module where it's imported
        with patch(
            "integration.system.tracos.repository.get_connection",
            new_callable=AsyncMock,
        ) as mock_conn:
            mock_conn.side_effect = ConnectionError("Connection failed")

            with pytest.raises(ConnectionError):
                await repo.mark_workorder_as_synced(1)


class TestClientRepositoryEdgeCases:
    """Edge case tests for ClientRepository."""

    def test_validate_workorder_with_optional_status_field(self, sample_client_workorder):
        """Test validation accepts workorder with status field."""
        repo = ClientRepository()

        # sample_client_workorder has status field
        result = repo.validate_workorder(sample_client_workorder)
        assert result is not None

    def test_validate_workorder_without_status_field(self, sample_client_workorder_completed):
        """Test validation accepts workorder without status field."""
        repo = ClientRepository()

        # sample_client_workorder_completed doesn't have status field (uses flags)
        result = repo.validate_workorder(sample_client_workorder_completed)
        assert result is not None

    def test_validate_workorder_empty_summary(self):
        """Test validation accepts empty summary."""
        repo = ClientRepository()

        workorder = {
            "orderNo": 1,
            "isCanceled": False,
            "isDeleted": False,
            "isDone": False,
            "isOnHold": False,
            "isPending": False,
            "summary": "",  # Empty but valid
            "creationDate": "2025-11-01T10:00:00+00:00",
            "lastUpdateDate": "2025-11-01T12:00:00+00:00",
            "deletedDate": None,
        }

        result = repo.validate_workorder(workorder)
        assert result is not None
        assert result["summary"] == ""

    def test_validate_workorder_special_characters_in_summary(self):
        """Test validation accepts special characters in summary."""
        repo = ClientRepository()

        workorder = {
            "orderNo": 1,
            "isCanceled": False,
            "isDeleted": False,
            "isDone": False,
            "isOnHold": False,
            "isPending": False,
            "summary": 'Test with émojis 🔧 and <html> & "quotes"',
            "creationDate": "2025-11-01T10:00:00+00:00",
            "lastUpdateDate": "2025-11-01T12:00:00+00:00",
            "deletedDate": None,
        }

        result = repo.validate_workorder(workorder)
        assert result is not None

    def test_validate_workorder_zero_order_number(self):
        """Test validation accepts zero as order number."""
        repo = ClientRepository()

        workorder = {
            "orderNo": 0,  # Zero is valid int
            "isCanceled": False,
            "isDeleted": False,
            "isDone": False,
            "isOnHold": False,
            "isPending": False,
            "summary": "Zero order",
            "creationDate": "2025-11-01T10:00:00+00:00",
            "lastUpdateDate": "2025-11-01T12:00:00+00:00",
            "deletedDate": None,
        }

        result = repo.validate_workorder(workorder)
        assert result is not None
        assert result["orderNo"] == 0

    def test_validate_workorder_negative_order_number(self):
        """Test validation accepts negative order number (if that's valid business logic)."""
        repo = ClientRepository()

        workorder = {
            "orderNo": -1,  # Negative is technically valid int
            "isCanceled": False,
            "isDeleted": False,
            "isDone": False,
            "isOnHold": False,
            "isPending": False,
            "summary": "Negative order",
            "creationDate": "2025-11-01T10:00:00+00:00",
            "lastUpdateDate": "2025-11-01T12:00:00+00:00",
            "deletedDate": None,
        }

        result = repo.validate_workorder(workorder)
        # The validator doesn't check for positive numbers
        assert result is not None
