"""
Pytest configuration and fixtures for TracOS ↔ Client Integration tests.

This module provides:
- Async test configuration
- Mock MongoDB fixtures
- Sample workorder data fixtures
- Temporary directory fixtures for filesystem tests
"""

import pytest
import asyncio
import json
import tempfile
import shutil
from pathlib import Path
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Any, AsyncGenerator
from unittest.mock import AsyncMock, MagicMock, patch


# Configure pytest-asyncio
pytest_plugins = ('pytest_asyncio',)


# =============================================================================
# Sample Data Fixtures
# =============================================================================

@pytest.fixture
def sample_client_workorder() -> Dict[str, Any]:
    """Valid client workorder in expected format."""
    return {
        "orderNo": 100,
        "status": "NEW",
        "isCanceled": False,
        "isDeleted": False,
        "isDone": False,
        "isOnHold": False,
        "isPending": False,
        "summary": "Test workorder #100",
        "creationDate": "2025-11-01T10:00:00+00:00",
        "lastUpdateDate": "2025-11-01T12:00:00+00:00",
        "deletedDate": None
    }


@pytest.fixture
def sample_client_workorder_completed() -> Dict[str, Any]:
    """Client workorder with completed status (using flags)."""
    return {
        "orderNo": 101,
        "isCanceled": False,
        "isDeleted": False,
        "isDone": True,
        "isOnHold": False,
        "isPending": False,
        "summary": "Completed workorder #101",
        "creationDate": "2025-11-01T10:00:00+00:00",
        "lastUpdateDate": "2025-11-01T15:00:00+00:00",
        "deletedDate": None
    }


@pytest.fixture
def sample_client_workorder_deleted() -> Dict[str, Any]:
    """Client workorder that is deleted."""
    return {
        "orderNo": 102,
        "status": "DELETED",
        "isCanceled": False,
        "isDeleted": True,
        "isDone": False,
        "isOnHold": False,
        "isPending": False,
        "summary": "Deleted workorder #102",
        "creationDate": "2025-11-01T10:00:00+00:00",
        "lastUpdateDate": "2025-11-01T16:00:00+00:00",
        "deletedDate": "2025-11-01T16:00:00+00:00"
    }


@pytest.fixture
def sample_tracos_workorder() -> Dict[str, Any]:
    """Valid TracOS workorder from MongoDB."""
    return {
        "_id": "692cf6d50b12b168f2f7cc18",
        "number": 200,
        "status": "completed",
        "title": "TracOS workorder #200",
        "description": "Description for TracOS workorder #200",
        "createdAt": datetime(2025, 11, 2, 2, 0, 53, 670000, tzinfo=timezone.utc),
        "updatedAt": datetime(2025, 11, 2, 3, 0, 53, 670000, tzinfo=timezone.utc),
        "deleted": False,
        "isSynced": False
    }


@pytest.fixture
def sample_tracos_workorder_pending() -> Dict[str, Any]:
    """TracOS workorder with pending status."""
    return {
        "_id": "692cf6d50b12b168f2f7cc19",
        "number": 201,
        "status": "pending",
        "title": "Pending TracOS workorder #201",
        "description": "Pending workorder description",
        "createdAt": datetime(2025, 11, 3, 10, 0, 0, tzinfo=timezone.utc),
        "updatedAt": datetime(2025, 11, 3, 11, 0, 0, tzinfo=timezone.utc),
        "deleted": False,
        "isSynced": False
    }


@pytest.fixture
def sample_tracos_workorder_deleted() -> Dict[str, Any]:
    """TracOS workorder that is deleted."""
    return {
        "_id": "692cf6d50b12b168f2f7cc20",
        "number": 202,
        "status": "deleted",
        "title": "Deleted TracOS workorder #202",
        "description": "Deleted workorder description",
        "createdAt": datetime(2025, 11, 1, 8, 0, 0, tzinfo=timezone.utc),
        "updatedAt": datetime(2025, 11, 4, 9, 0, 0, tzinfo=timezone.utc),
        "deleted": True,
        "isSynced": False
    }


# =============================================================================
# Edge Case Fixtures
# =============================================================================

@pytest.fixture
def malformed_client_workorders() -> List[Dict[str, Any]]:
    """Collection of malformed workorders for validation testing."""
    return [
        # Missing required field
        {
            "orderNo": 1,
            "isCanceled": False,
            # Missing isDeleted
            "isDone": False,
            "isOnHold": False,
            "isPending": False,
            "summary": "Missing isDeleted",
            "creationDate": "2025-11-01T10:00:00+00:00",
            "lastUpdateDate": "2025-11-01T12:00:00+00:00",
            "deletedDate": None
        },
        # Wrong type for orderNo
        {
            "orderNo": "not_an_int",
            "isCanceled": False,
            "isDeleted": False,
            "isDone": False,
            "isOnHold": False,
            "isPending": False,
            "summary": "Wrong type",
            "creationDate": "2025-11-01T10:00:00+00:00",
            "lastUpdateDate": "2025-11-01T12:00:00+00:00",
            "deletedDate": None
        },
        # Invalid date format
        {
            "orderNo": 2,
            "isCanceled": False,
            "isDeleted": False,
            "isDone": False,
            "isOnHold": False,
            "isPending": False,
            "summary": "Invalid date",
            "creationDate": "not-a-date",
            "lastUpdateDate": "2025-11-01T12:00:00+00:00",
            "deletedDate": None
        },
        # isDeleted true but deletedDate is non-null invalid
        {
            "orderNo": 3,
            "isCanceled": False,
            "isDeleted": True,
            "isDone": False,
            "isOnHold": False,
            "isPending": False,
            "summary": "Deleted but invalid deletedDate",
            "creationDate": "2025-11-01T10:00:00+00:00",
            "lastUpdateDate": "2025-11-01T12:00:00+00:00",
            "deletedDate": "invalid-date"
        },
        # deletedDate present but isDeleted is False
        {
            "orderNo": 4,
            "isCanceled": False,
            "isDeleted": False,
            "isDone": False,
            "isOnHold": False,
            "isPending": False,
            "summary": "Not deleted but has deletedDate",
            "creationDate": "2025-11-01T10:00:00+00:00",
            "lastUpdateDate": "2025-11-01T12:00:00+00:00",
            "deletedDate": "2025-11-01T16:00:00+00:00"
        }
    ]


@pytest.fixture
def edge_case_dates() -> List[Dict[str, Any]]:
    """Various date formats for testing date parsing robustness."""
    return [
        {"input": "2025-11-01T10:00:00+00:00", "valid": True},
        {"input": "2025-11-01T10:00:00Z", "valid": True},
        {"input": "2025-11-01T10:00:00", "valid": True},  # Naive datetime
        {"input": "2025-11-01T10:00:00.123456+00:00", "valid": True},  # With microseconds
        {"input": "2025-11-01", "valid": True},  # Date only
        {"input": "", "valid": False},  # Empty string
        {"input": None, "valid": False},  # None
        {"input": "invalid", "valid": False},  # Invalid format
        {"input": "2025-13-45T99:99:99", "valid": False},  # Invalid values
    ]


# =============================================================================
# Filesystem Fixtures
# =============================================================================

@pytest.fixture
def temp_data_dirs():
    """Create temporary inbound and outbound directories for testing."""
    temp_dir = tempfile.mkdtemp()
    inbound_dir = Path(temp_dir) / "inbound"
    outbound_dir = Path(temp_dir) / "outbound"
    inbound_dir.mkdir(parents=True)
    outbound_dir.mkdir(parents=True)
    
    yield {
        "root": Path(temp_dir),
        "inbound": inbound_dir,
        "outbound": outbound_dir
    }
    
    # Cleanup
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def populated_inbound_dir(temp_data_dirs, sample_client_workorder, sample_client_workorder_completed):
    """Inbound directory with sample workorder JSON files."""
    inbound_dir = temp_data_dirs["inbound"]
    
    # Write sample workorders
    workorders = [sample_client_workorder, sample_client_workorder_completed]
    for wo in workorders:
        filepath = inbound_dir / f"{wo['orderNo']}.json"
        with open(filepath, 'w') as f:
            json.dump(wo, f, indent=2)
    
    return inbound_dir


@pytest.fixture
def inbound_dir_with_corrupted_json(temp_data_dirs, sample_client_workorder):
    """Inbound directory with both valid and corrupted JSON files."""
    inbound_dir = temp_data_dirs["inbound"]
    
    # Write valid workorder
    valid_path = inbound_dir / "100.json"
    with open(valid_path, 'w') as f:
        json.dump(sample_client_workorder, f, indent=2)
    
    # Write corrupted JSON
    corrupted_path = inbound_dir / "corrupted.json"
    with open(corrupted_path, 'w') as f:
        f.write("{invalid json content")
    
    return inbound_dir


# =============================================================================
# Mock MongoDB Fixtures
# =============================================================================

@pytest.fixture
def mock_collection():
    """Create a mock MongoDB collection with async methods."""
    collection = MagicMock()
    
    # Storage for "database"
    _storage: List[Dict] = []
    
    async def mock_find_one(query):
        for doc in _storage:
            if all(doc.get(k) == v for k, v in query.items()):
                return doc
        return None
    
    async def mock_insert_one(doc):
        _storage.append(doc.copy())
        result = MagicMock()
        result.inserted_id = doc.get("_id", "mock_id")
        return result
    
    async def mock_update_one(query, update):
        for i, doc in enumerate(_storage):
            if all(doc.get(k) == v for k, v in query.items()):
                if "$set" in update:
                    _storage[i].update(update["$set"])
                result = MagicMock()
                result.modified_count = 1
                return result
        result = MagicMock()
        result.modified_count = 0
        return result
    
    def mock_find(query):
        """Returns an async iterator of matching documents."""
        class AsyncCursor:
            def __init__(self, docs, query):
                self._docs = [d for d in docs if self._matches(d, query)]
                self._index = 0
            
            def _matches(self, doc, query):
                for k, v in query.items():
                    if isinstance(v, dict) and "$ne" in v:
                        if doc.get(k) == v["$ne"]:
                            return False
                    elif doc.get(k) != v:
                        return False
                return True
            
            def __aiter__(self):
                return self
            
            async def __anext__(self):
                if self._index >= len(self._docs):
                    raise StopAsyncIteration
                doc = self._docs[self._index]
                self._index += 1
                return doc
        
        return AsyncCursor(_storage, query)
    
    collection.find_one = mock_find_one
    collection.insert_one = mock_insert_one
    collection.update_one = mock_update_one
    collection.find = mock_find
    collection._storage = _storage  # Expose for test manipulation
    
    return collection


@pytest.fixture
def mock_database(mock_collection):
    """Create a mock MongoDB database."""
    database = MagicMock()
    database.__getitem__ = MagicMock(return_value=mock_collection)
    
    async def mock_command(cmd):
        if cmd == "ping":
            return {"ok": 1}
        return {}
    
    database.command = mock_command
    return database


@pytest.fixture
def mock_db_connection(mock_database, mock_collection):
    """Patch the database connection to return mock database."""
    # Patch in the module where it's imported, not where it's defined
    with patch('integration.system.tracos.repository.get_connection', new_callable=AsyncMock) as mock_get_conn:
        mock_get_conn.return_value = mock_database
        with patch('integration.system.tracos.repository.get_collection') as mock_get_coll:
            mock_get_coll.return_value = mock_collection
            yield {
                "get_connection": mock_get_conn,
                "get_collection": mock_get_coll,
                "database": mock_database,
                "collection": mock_collection
            }


# =============================================================================
# Status Mapping Test Data
# =============================================================================

@pytest.fixture
def client_to_tracos_status_cases() -> List[Dict[str, Any]]:
    """Test cases for client to TracOS status mapping."""
    return [
        {"status": "NEW", "flags": None, "expected": "created"},
        {"status": "PENDING", "flags": None, "expected": "pending"},
        {"status": "IN_PROGRESS", "flags": None, "expected": "in_progress"},
        {"status": "ON_HOLD", "flags": None, "expected": "on_hold"},
        {"status": "COMPLETED", "flags": None, "expected": "completed"},
        {"status": "CANCELLED", "flags": None, "expected": "cancelled"},
        {"status": "CANCELED", "flags": None, "expected": "cancelled"},  # Alternate spelling
        {"status": "DELETED", "flags": None, "expected": "deleted"},
        # Flag-based mapping (backward compatibility)
        {"status": None, "flags": {"isDone": True}, "expected": "completed"},
        {"status": None, "flags": {"isCanceled": True}, "expected": "cancelled"},
        {"status": None, "flags": {"isOnHold": True}, "expected": "on_hold"},
        {"status": None, "flags": {"isPending": True}, "expected": "pending"},
        {"status": None, "flags": {"isDeleted": True}, "expected": "deleted"},
        # Default case
        {"status": None, "flags": {}, "expected": "in_progress"},
        {"status": None, "flags": None, "expected": "in_progress"},
        # Unknown status falls back to flags
        {"status": "UNKNOWN_STATUS", "flags": {"isDone": True}, "expected": "completed"},
    ]


@pytest.fixture
def tracos_to_client_status_cases() -> List[Dict[str, Any]]:
    """Test cases for TracOS to client status mapping."""
    return [
        {"status": "created", "expected_status": "NEW", "expected_flags": {}},
        {"status": "pending", "expected_status": "PENDING", "expected_flags": {"isPending": True}},
        {"status": "in_progress", "expected_status": "IN_PROGRESS", "expected_flags": {}},
        {"status": "on_hold", "expected_status": "ON_HOLD", "expected_flags": {"isOnHold": True}},
        {"status": "completed", "expected_status": "COMPLETED", "expected_flags": {"isDone": True}},
        {"status": "cancelled", "expected_status": "CANCELLED", "expected_flags": {"isCanceled": True}},
        {"status": "deleted", "expected_status": "DELETED", "expected_flags": {}},
        # Edge cases
        {"status": None, "expected_status": None, "expected_flags": {}},
        {"status": "", "expected_status": None, "expected_flags": {}},
    ]

