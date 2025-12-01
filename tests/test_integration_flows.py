"""
End-to-end integration tests for the complete sync flows.

These tests verify:
- Complete Client → TracOS sync flow
- Complete TracOS → Client sync flow
- Error handling and resilience
- Data integrity throughout the pipeline
"""

import pytest
import json
from pathlib import Path
from datetime import datetime, timezone
from unittest.mock import patch, MagicMock, AsyncMock

from integration.flows.client_to_tracos import ClientToTracOSFlow
from integration.flows.tracos_to_client import TracOSToClientFlow


class TestClientToTracOSFlow:
    """End-to-end tests for Client → TracOS synchronization."""
    
    @pytest.mark.asyncio
    async def test_sync_processes_all_workorders(self, populated_inbound_dir, mock_db_connection):
        """Test that sync processes all valid workorders from directory."""
        flow = ClientToTracOSFlow()
        
        await flow.sync(populated_inbound_dir)
        
        # Should have saved 2 workorders
        collection = mock_db_connection["collection"]
        assert len(collection._storage) == 2
    
    @pytest.mark.asyncio
    async def test_sync_handles_nonexistent_directory(self, temp_data_dirs, mock_db_connection):
        """Test that sync handles nonexistent directory gracefully."""
        flow = ClientToTracOSFlow()
        nonexistent = temp_data_dirs["root"] / "nonexistent"
        
        # Should not raise, should log error
        await flow.sync(nonexistent)
        
        # No workorders should be saved
        collection = mock_db_connection["collection"]
        assert len(collection._storage) == 0
    
    @pytest.mark.asyncio
    async def test_sync_skips_invalid_workorders(self, temp_data_dirs, mock_db_connection):
        """Test that sync skips invalid workorders and continues."""
        inbound_dir = temp_data_dirs["inbound"]
        
        # Write valid workorder
        valid = {
            "orderNo": 1,
            "isCanceled": False,
            "isDeleted": False,
            "isDone": False,
            "isOnHold": False,
            "isPending": False,
            "summary": "Valid workorder",
            "creationDate": "2025-11-01T10:00:00+00:00",
            "lastUpdateDate": "2025-11-01T12:00:00+00:00",
            "deletedDate": None
        }
        with open(inbound_dir / "1.json", 'w') as f:
            json.dump(valid, f)
        
        # Write invalid workorder (missing required field)
        invalid = {
            "orderNo": 2,
            # Missing other required fields
        }
        with open(inbound_dir / "2.json", 'w') as f:
            json.dump(invalid, f)
        
        flow = ClientToTracOSFlow()
        await flow.sync(inbound_dir)
        
        # Should only save the valid workorder
        collection = mock_db_connection["collection"]
        assert len(collection._storage) == 1
        assert collection._storage[0]["number"] == 1
    
    @pytest.mark.asyncio
    async def test_sync_handles_corrupted_json(self, inbound_dir_with_corrupted_json, mock_db_connection):
        """Test that sync handles corrupted JSON files gracefully."""
        flow = ClientToTracOSFlow()
        
        await flow.sync(inbound_dir_with_corrupted_json)
        
        # Should save only valid workorder
        collection = mock_db_connection["collection"]
        assert len(collection._storage) == 1
    
    @pytest.mark.asyncio
    async def test_sync_translates_data_correctly(self, temp_data_dirs, mock_db_connection):
        """Test that sync translates data correctly to TracOS format."""
        inbound_dir = temp_data_dirs["inbound"]
        
        # Write workorder with specific values
        workorder = {
            "orderNo": 42,
            "status": "COMPLETED",
            "isCanceled": False,
            "isDeleted": False,
            "isDone": True,
            "isOnHold": False,
            "isPending": False,
            "summary": "Test translation",
            "creationDate": "2025-11-01T10:00:00+00:00",
            "lastUpdateDate": "2025-11-01T15:00:00+00:00",
            "deletedDate": None
        }
        with open(inbound_dir / "42.json", 'w') as f:
            json.dump(workorder, f)
        
        flow = ClientToTracOSFlow()
        await flow.sync(inbound_dir)
        
        # Verify translation
        collection = mock_db_connection["collection"]
        assert len(collection._storage) == 1
        
        saved = collection._storage[0]
        assert saved["number"] == 42
        assert saved["status"] == "completed"
        assert saved["title"] == "Test translation"
        assert saved["deleted"] is False
        assert isinstance(saved["createdAt"], datetime)
        assert isinstance(saved["updatedAt"], datetime)
    
    @pytest.mark.asyncio
    async def test_sync_updates_existing_workorder(self, temp_data_dirs, mock_db_connection):
        """Test that sync updates existing workorder when changed."""
        inbound_dir = temp_data_dirs["inbound"]
        collection = mock_db_connection["collection"]
        
        # Pre-populate with existing workorder
        collection._storage.append({
            "number": 1,
            "status": "created",
            "title": "Original",
            "description": "Original",
            "createdAt": datetime(2025, 11, 1, tzinfo=timezone.utc),
            "updatedAt": datetime(2025, 11, 1, tzinfo=timezone.utc),
            "deleted": False
        })
        
        # Write updated workorder
        updated = {
            "orderNo": 1,
            "status": "COMPLETED",
            "isCanceled": False,
            "isDeleted": False,
            "isDone": True,
            "isOnHold": False,
            "isPending": False,
            "summary": "Updated",
            "creationDate": "2025-11-01T10:00:00+00:00",
            "lastUpdateDate": "2025-11-02T10:00:00+00:00",
            "deletedDate": None
        }
        with open(inbound_dir / "1.json", 'w') as f:
            json.dump(updated, f)
        
        flow = ClientToTracOSFlow()
        await flow.sync(inbound_dir)
        
        # Should still have 1 workorder (updated, not duplicated)
        assert len(collection._storage) == 1
        assert collection._storage[0]["status"] == "completed"
        assert collection._storage[0]["title"] == "Updated"


class TestTracOSToClientFlow:
    """End-to-end tests for TracOS → Client synchronization."""
    
    @pytest.mark.asyncio
    async def test_sync_exports_all_unsynced(self, temp_data_dirs, mock_db_connection):
        """Test that sync exports all unsynced workorders."""
        collection = mock_db_connection["collection"]
        outbound_dir = temp_data_dirs["outbound"]
        
        # Add unsynced workorders
        collection._storage.extend([
            {
                "number": 1, "status": "completed", "title": "Test 1",
                "description": "Desc 1",
                "createdAt": datetime.now(timezone.utc),
                "updatedAt": datetime.now(timezone.utc),
                "deleted": False, "isSynced": False
            },
            {
                "number": 2, "status": "pending", "title": "Test 2",
                "description": "Desc 2",
                "createdAt": datetime.now(timezone.utc),
                "updatedAt": datetime.now(timezone.utc),
                "deleted": False, "isSynced": False
            },
        ])
        
        flow = TracOSToClientFlow()
        await flow.sync(outbound_dir)
        
        # Should have 2 JSON files
        json_files = list(outbound_dir.glob("*.json"))
        assert len(json_files) == 2
    
    @pytest.mark.asyncio
    async def test_sync_skips_already_synced(self, temp_data_dirs, mock_db_connection):
        """Test that sync skips already synced workorders."""
        collection = mock_db_connection["collection"]
        outbound_dir = temp_data_dirs["outbound"]
        
        # Add mix of synced and unsynced
        collection._storage.extend([
            {
                "number": 1, "status": "completed", "title": "Unsynced",
                "description": "Desc",
                "createdAt": datetime.now(timezone.utc),
                "updatedAt": datetime.now(timezone.utc),
                "deleted": False, "isSynced": False
            },
            {
                "number": 2, "status": "completed", "title": "Already synced",
                "description": "Desc",
                "createdAt": datetime.now(timezone.utc),
                "updatedAt": datetime.now(timezone.utc),
                "deleted": False, "isSynced": True
            },
        ])
        
        flow = TracOSToClientFlow()
        await flow.sync(outbound_dir)
        
        # Should only export 1 file
        json_files = list(outbound_dir.glob("*.json"))
        assert len(json_files) == 1
        assert json_files[0].name == "1.json"
    
    @pytest.mark.asyncio
    async def test_sync_marks_workorders_as_synced(self, temp_data_dirs, mock_db_connection):
        """Test that sync marks workorders as synced after export."""
        collection = mock_db_connection["collection"]
        outbound_dir = temp_data_dirs["outbound"]
        
        collection._storage.append({
            "number": 1, "status": "completed", "title": "Test",
            "description": "Desc",
            "createdAt": datetime.now(timezone.utc),
            "updatedAt": datetime.now(timezone.utc),
            "deleted": False, "isSynced": False
        })
        
        flow = TracOSToClientFlow()
        await flow.sync(outbound_dir)
        
        # Workorder should be marked as synced
        assert collection._storage[0]["isSynced"] is True
        assert "syncedAt" in collection._storage[0]
    
    @pytest.mark.asyncio
    async def test_sync_creates_output_directory(self, temp_data_dirs, mock_db_connection):
        """Test that sync creates output directory if it doesn't exist."""
        collection = mock_db_connection["collection"]
        new_outbound = temp_data_dirs["root"] / "new_output"
        
        collection._storage.append({
            "number": 1, "status": "completed", "title": "Test",
            "description": "Desc",
            "createdAt": datetime.now(timezone.utc),
            "updatedAt": datetime.now(timezone.utc),
            "deleted": False, "isSynced": False
        })
        
        flow = TracOSToClientFlow()
        await flow.sync(new_outbound)
        
        assert new_outbound.exists()
        assert (new_outbound / "1.json").exists()
    
    @pytest.mark.asyncio
    async def test_sync_translates_data_correctly(self, temp_data_dirs, mock_db_connection):
        """Test that sync translates data correctly to Client format."""
        collection = mock_db_connection["collection"]
        outbound_dir = temp_data_dirs["outbound"]
        
        collection._storage.append({
            "number": 42, "status": "completed", "title": "TracOS workorder",
            "description": "TracOS description",
            "createdAt": datetime(2025, 11, 1, 10, 0, 0, tzinfo=timezone.utc),
            "updatedAt": datetime(2025, 11, 1, 15, 0, 0, tzinfo=timezone.utc),
            "deleted": False, "isSynced": False
        })
        
        flow = TracOSToClientFlow()
        await flow.sync(outbound_dir)
        
        # Read exported file
        with open(outbound_dir / "42.json") as f:
            exported = json.load(f)
        
        assert exported["orderNo"] == 42
        assert exported["status"] == "COMPLETED"
        assert exported["summary"] == "TracOS workorder"
        assert exported["isDone"] is True
        assert exported["isDeleted"] is False
        assert "creationDate" in exported
        assert "lastUpdateDate" in exported
    
    @pytest.mark.asyncio
    async def test_sync_skips_invalid_workorders(self, temp_data_dirs, mock_db_connection):
        """Test that sync skips workorders that fail validation."""
        collection = mock_db_connection["collection"]
        outbound_dir = temp_data_dirs["outbound"]
        
        # Add workorder missing required field
        collection._storage.append({
            "number": 1, "status": "completed",
            # Missing title, description, dates
            "deleted": False, "isSynced": False
        })
        
        flow = TracOSToClientFlow()
        await flow.sync(outbound_dir)
        
        # Should not export invalid workorder
        json_files = list(outbound_dir.glob("*.json"))
        assert len(json_files) == 0
    
    def test_validate_workorder_valid(self, sample_tracos_workorder):
        """Test validation of valid TracOS workorder."""
        flow = TracOSToClientFlow()
        result = flow.validate_workorder(sample_tracos_workorder)
        assert result is True
    
    def test_validate_workorder_missing_field(self):
        """Test validation rejects workorder with missing required field."""
        flow = TracOSToClientFlow()
        
        invalid = {
            "number": 1,
            "status": "completed",
            # Missing title, description, dates, deleted
        }
        
        result = flow.validate_workorder(invalid)
        assert result is False
    
    def test_validate_workorder_none_value(self):
        """Test validation rejects workorder with None for required field."""
        flow = TracOSToClientFlow()
        
        invalid = {
            "number": 1,
            "status": "completed",
            "title": None,  # None is not allowed
            "description": "Desc",
            "createdAt": datetime.now(timezone.utc),
            "updatedAt": datetime.now(timezone.utc),
            "deleted": False
        }
        
        result = flow.validate_workorder(invalid)
        assert result is False


class TestIntegrationEdgeCases:
    """Edge case tests for integration flows."""
    
    @pytest.mark.asyncio
    async def test_empty_inbound_directory(self, temp_data_dirs, mock_db_connection):
        """Test handling of empty inbound directory."""
        flow = ClientToTracOSFlow()
        inbound_dir = temp_data_dirs["inbound"]
        
        await flow.sync(inbound_dir)
        
        # Should complete without error
        collection = mock_db_connection["collection"]
        assert len(collection._storage) == 0
    
    @pytest.mark.asyncio
    async def test_large_batch_processing(self, temp_data_dirs, mock_db_connection):
        """Test processing a large batch of workorders."""
        inbound_dir = temp_data_dirs["inbound"]
        
        # Create 50 workorders
        for i in range(50):
            workorder = {
                "orderNo": i,
                "isCanceled": False,
                "isDeleted": False,
                "isDone": i % 3 == 0,  # Every 3rd is done
                "isOnHold": False,
                "isPending": i % 5 == 0,  # Every 5th is pending
                "summary": f"Workorder #{i}",
                "creationDate": "2025-11-01T10:00:00+00:00",
                "lastUpdateDate": "2025-11-01T12:00:00+00:00",
                "deletedDate": None
            }
            with open(inbound_dir / f"{i}.json", 'w') as f:
                json.dump(workorder, f)
        
        flow = ClientToTracOSFlow()
        await flow.sync(inbound_dir)
        
        # All 50 should be processed
        collection = mock_db_connection["collection"]
        assert len(collection._storage) == 50
    
    @pytest.mark.asyncio
    async def test_workorder_with_special_characters(self, temp_data_dirs, mock_db_connection):
        """Test workorder with special characters in title/summary."""
        inbound_dir = temp_data_dirs["inbound"]
        
        workorder = {
            "orderNo": 1,
            "isCanceled": False,
            "isDeleted": False,
            "isDone": False,
            "isOnHold": False,
            "isPending": False,
            "summary": "Test with émojis 🔧, <html> tags, & \"quotes\", null\x00bytes",
            "creationDate": "2025-11-01T10:00:00+00:00",
            "lastUpdateDate": "2025-11-01T12:00:00+00:00",
            "deletedDate": None
        }
        with open(inbound_dir / "1.json", 'w') as f:
            json.dump(workorder, f)
        
        flow = ClientToTracOSFlow()
        await flow.sync(inbound_dir)
        
        collection = mock_db_connection["collection"]
        assert len(collection._storage) == 1
        assert "émojis" in collection._storage[0]["title"]
    
    @pytest.mark.asyncio  
    async def test_concurrent_updates_same_workorder(self, temp_data_dirs, mock_db_connection):
        """Test that multiple files for same workorder number are handled."""
        inbound_dir = temp_data_dirs["inbound"]
        collection = mock_db_connection["collection"]
        
        # Pre-populate existing workorder
        collection._storage.append({
            "number": 1,
            "status": "created",
            "title": "Original",
            "description": "Original",
            "createdAt": datetime.now(timezone.utc),
            "updatedAt": datetime.now(timezone.utc),
            "deleted": False
        })
        
        # Write workorder with same number
        workorder = {
            "orderNo": 1,
            "status": "COMPLETED",
            "isCanceled": False,
            "isDeleted": False,
            "isDone": True,
            "isOnHold": False,
            "isPending": False,
            "summary": "Updated",
            "creationDate": "2025-11-01T10:00:00+00:00",
            "lastUpdateDate": "2025-11-02T10:00:00+00:00",
            "deletedDate": None
        }
        with open(inbound_dir / "1.json", 'w') as f:
            json.dump(workorder, f)
        
        flow = ClientToTracOSFlow()
        await flow.sync(inbound_dir)
        
        # Should have updated, not duplicated
        assert len(collection._storage) == 1
        assert collection._storage[0]["status"] == "completed"


class TestFlowDataIntegrity:
    """Tests for data integrity across the complete flow."""
    
    @pytest.mark.asyncio
    async def test_round_trip_data_integrity(self, temp_data_dirs, mock_db_connection):
        """Test that data maintains integrity through round-trip sync."""
        inbound_dir = temp_data_dirs["inbound"]
        outbound_dir = temp_data_dirs["outbound"]
        collection = mock_db_connection["collection"]
        
        # Create original client workorder
        original = {
            "orderNo": 999,
            "status": "COMPLETED",
            "isCanceled": False,
            "isDeleted": False,
            "isDone": True,
            "isOnHold": False,
            "isPending": False,
            "summary": "Round trip test",
            "creationDate": "2025-11-01T10:00:00+00:00",
            "lastUpdateDate": "2025-11-01T15:00:00+00:00",
            "deletedDate": None
        }
        with open(inbound_dir / "999.json", 'w') as f:
            json.dump(original, f)
        
        # Sync client → TracOS
        client_to_tracos = ClientToTracOSFlow()
        await client_to_tracos.sync(inbound_dir)
        
        # Reset isSynced for next flow
        collection._storage[0]["isSynced"] = False
        
        # Sync TracOS → Client
        tracos_to_client = TracOSToClientFlow()
        await tracos_to_client.sync(outbound_dir)
        
        # Read exported file
        with open(outbound_dir / "999.json") as f:
            exported = json.load(f)
        
        # Verify key fields are preserved
        assert exported["orderNo"] == original["orderNo"]
        assert exported["summary"] == original["summary"]
        assert exported["isDeleted"] == original["isDeleted"]
        assert exported["status"] == original["status"]
    
    @pytest.mark.asyncio
    async def test_deleted_workorder_round_trip(self, temp_data_dirs, mock_db_connection):
        """Test that deleted status is preserved through round-trip."""
        inbound_dir = temp_data_dirs["inbound"]
        outbound_dir = temp_data_dirs["outbound"]
        collection = mock_db_connection["collection"]
        
        # Create deleted workorder
        deleted = {
            "orderNo": 1,
            "status": "DELETED",
            "isCanceled": False,
            "isDeleted": True,
            "isDone": False,
            "isOnHold": False,
            "isPending": False,
            "summary": "Deleted workorder",
            "creationDate": "2025-11-01T10:00:00+00:00",
            "lastUpdateDate": "2025-11-01T16:00:00+00:00",
            "deletedDate": "2025-11-01T16:00:00+00:00"
        }
        with open(inbound_dir / "1.json", 'w') as f:
            json.dump(deleted, f)
        
        # Sync client → TracOS
        client_to_tracos = ClientToTracOSFlow()
        await client_to_tracos.sync(inbound_dir)
        
        # Verify TracOS has deleted flag
        assert collection._storage[0]["deleted"] is True
        assert collection._storage[0]["status"] == "deleted"
        
        # Reset isSynced for next flow
        collection._storage[0]["isSynced"] = False
        
        # Sync TracOS → Client
        tracos_to_client = TracOSToClientFlow()
        await tracos_to_client.sync(outbound_dir)
        
        with open(outbound_dir / "1.json") as f:
            exported = json.load(f)
        
        # Verify deleted status preserved
        assert exported["isDeleted"] is True
        assert exported["deletedDate"] is not None

