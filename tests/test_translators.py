"""
Tests for translation logic between Client and TracOS formats.

These tests verify:
- Correct field mapping between systems
- Status translation (enum and flag-based)
- Date parsing and formatting
- Edge cases and error handling
"""

import pytest
from datetime import datetime, timezone, timedelta

from integration.translators.client_to_tracos import translate_client_to_tracos, parse_datetime
from integration.translators.tracos_to_client import translate_tracos_to_client, _format_datetime


class TestClientToTracOSTranslator:
    """Tests for Client → TracOS translation."""
    
    def test_translate_basic_workorder(self, sample_client_workorder):
        """Test basic workorder translation with all required fields."""
        result = translate_client_to_tracos(sample_client_workorder)
        
        assert result['number'] == 100
        assert result['title'] == "Test workorder #100"
        assert result['status'] == 'created'  # NEW → created
        assert result['deleted'] is False
        assert isinstance(result['createdAt'], datetime)
        assert isinstance(result['updatedAt'], datetime)
    
    def test_translate_completed_workorder_with_flag(self, sample_client_workorder_completed):
        """Test translation when status is determined by flags (backward compatibility)."""
        result = translate_client_to_tracos(sample_client_workorder_completed)
        
        assert result['number'] == 101
        assert result['status'] == 'completed'  # isDone: true → completed
        assert result['deleted'] is False
    
    def test_translate_deleted_workorder(self, sample_client_workorder_deleted):
        """Test translation of deleted workorder."""
        result = translate_client_to_tracos(sample_client_workorder_deleted)
        
        assert result['number'] == 102
        assert result['status'] == 'deleted'
        assert result['deleted'] is True
    
    def test_description_field_populated(self, sample_client_workorder):
        """Test that description field is populated from summary."""
        result = translate_client_to_tracos(sample_client_workorder)
        
        # description field is required by TracOSWorkorder TypedDict
        assert 'description' in result, "description field is missing from translation"
        assert result['description'] == sample_client_workorder['summary']
    
    def test_status_enum_takes_priority_over_flags(self):
        """Test that status enum value takes priority over boolean flags."""
        workorder = {
            "orderNo": 1,
            "status": "COMPLETED",  # Enum says completed
            "isCanceled": False,
            "isDeleted": False,
            "isDone": False,  # Flag says NOT done
            "isOnHold": True,  # Flag says on hold
            "isPending": False,
            "summary": "Priority test",
            "creationDate": "2025-11-01T10:00:00+00:00",
            "lastUpdateDate": "2025-11-01T12:00:00+00:00",
            "deletedDate": None
        }
        
        result = translate_client_to_tracos(workorder)
        # Status enum should take priority
        assert result['status'] == 'completed'
    
    def test_empty_summary_becomes_empty_title(self):
        """Test handling of empty or missing summary."""
        workorder = {
            "orderNo": 1,
            "isCanceled": False,
            "isDeleted": False,
            "isDone": False,
            "isOnHold": False,
            "isPending": False,
            "summary": "",
            "creationDate": "2025-11-01T10:00:00+00:00",
            "lastUpdateDate": "2025-11-01T12:00:00+00:00",
            "deletedDate": None
        }
        
        result = translate_client_to_tracos(workorder)
        assert result['title'] == ""
    
    def test_missing_summary_defaults_to_empty(self):
        """Test handling of missing summary field."""
        workorder = {
            "orderNo": 1,
            "isCanceled": False,
            "isDeleted": False,
            "isDone": False,
            "isOnHold": False,
            "isPending": False,
            # summary is missing
            "creationDate": "2025-11-01T10:00:00+00:00",
            "lastUpdateDate": "2025-11-01T12:00:00+00:00",
            "deletedDate": None
        }
        
        result = translate_client_to_tracos(workorder)
        assert result['title'] == ""


class TestParseDatetime:
    """Tests for datetime parsing function."""
    
    def test_parse_iso_datetime_with_timezone(self):
        """Test parsing ISO datetime with timezone offset."""
        result = parse_datetime("2025-11-01T10:00:00+00:00")
        
        assert isinstance(result, datetime)
        assert result.year == 2025
        assert result.month == 11
        assert result.day == 1
        assert result.hour == 10
        assert result.tzinfo is not None
    
    def test_parse_iso_datetime_with_z_suffix(self):
        """Test parsing ISO datetime with Z suffix (Zulu time)."""
        result = parse_datetime("2025-11-01T10:00:00Z")
        
        assert isinstance(result, datetime)
        assert result.tzinfo is not None
    
    def test_parse_naive_datetime_adds_utc(self):
        """Test that naive datetimes get UTC timezone added."""
        result = parse_datetime("2025-11-01T10:00:00")
        
        assert isinstance(result, datetime)
        assert result.tzinfo == timezone.utc
    
    def test_parse_datetime_with_microseconds(self):
        """Test parsing datetime with microseconds."""
        result = parse_datetime("2025-11-01T10:00:00.123456+00:00")
        
        assert isinstance(result, datetime)
        assert result.microsecond == 123456
    
    def test_parse_empty_string_returns_current_time(self):
        """Test that empty string returns current UTC time."""
        before = datetime.now(timezone.utc)
        result = parse_datetime("")
        after = datetime.now(timezone.utc)
        
        assert isinstance(result, datetime)
        assert before <= result <= after
    
    def test_parse_none_returns_current_time(self):
        """Test that None returns current UTC time."""
        before = datetime.now(timezone.utc)
        result = parse_datetime(None)
        after = datetime.now(timezone.utc)
        
        assert isinstance(result, datetime)
        assert before <= result <= after
    
    def test_parse_invalid_string_returns_current_time(self):
        """Test that invalid date string returns current UTC time."""
        before = datetime.now(timezone.utc)
        result = parse_datetime("not-a-valid-date")
        after = datetime.now(timezone.utc)
        
        assert isinstance(result, datetime)
        assert before <= result <= after
    
    def test_parse_date_only_string(self):
        """Test parsing date-only string (no time component)."""
        result = parse_datetime("2025-11-01")
        
        assert isinstance(result, datetime)
        assert result.year == 2025
        assert result.month == 11
        assert result.day == 1


class TestTracOSToClientTranslator:
    """Tests for TracOS → Client translation."""
    
    def test_translate_basic_workorder(self, sample_tracos_workorder):
        """Test basic workorder translation."""
        result = translate_tracos_to_client(sample_tracos_workorder)
        
        assert result['orderNo'] == 200
        assert result['summary'] == "TracOS workorder #200"
        assert result['status'] == 'COMPLETED'
        assert result['isDone'] is True
        assert result['isDeleted'] is False
        assert result['deletedDate'] is None
    
    def test_translate_pending_workorder(self, sample_tracos_workorder_pending):
        """Test translation of pending workorder."""
        result = translate_tracos_to_client(sample_tracos_workorder_pending)
        
        assert result['orderNo'] == 201
        assert result['status'] == 'PENDING'
        assert result['isPending'] is True
        assert result['isDone'] is False
    
    def test_translate_deleted_workorder(self, sample_tracos_workorder_deleted):
        """Test translation of deleted workorder sets deletedDate."""
        result = translate_tracos_to_client(sample_tracos_workorder_deleted)
        
        assert result['orderNo'] == 202
        assert result['isDeleted'] is True
        assert result['deletedDate'] is not None
        # deletedDate should be set to updatedAt when deleted
    
    def test_all_boolean_flags_present(self, sample_tracos_workorder):
        """Test that all required boolean flags are present in output."""
        result = translate_tracos_to_client(sample_tracos_workorder)
        
        required_flags = ['isCanceled', 'isDeleted', 'isDone', 'isOnHold', 'isPending']
        for flag in required_flags:
            assert flag in result, f"Missing required flag: {flag}"
            assert isinstance(result[flag], bool), f"Flag {flag} should be boolean"
    
    def test_dates_are_iso_strings(self, sample_tracos_workorder):
        """Test that dates are formatted as ISO strings."""
        result = translate_tracos_to_client(sample_tracos_workorder)
        
        assert isinstance(result['creationDate'], str)
        assert isinstance(result['lastUpdateDate'], str)
        # Should be parseable as ISO format
        datetime.fromisoformat(result['creationDate'])
        datetime.fromisoformat(result['lastUpdateDate'])
    
    def test_cancelled_status_mapping(self):
        """Test that cancelled status sets correct flags."""
        workorder = {
            "number": 1,
            "status": "cancelled",
            "title": "Cancelled workorder",
            "description": "Description",
            "createdAt": datetime.now(timezone.utc),
            "updatedAt": datetime.now(timezone.utc),
            "deleted": False
        }
        
        result = translate_tracos_to_client(workorder)
        
        assert result['status'] == 'CANCELLED'
        assert result['isCanceled'] is True
    
    def test_on_hold_status_mapping(self):
        """Test that on_hold status sets correct flags."""
        workorder = {
            "number": 1,
            "status": "on_hold",
            "title": "On hold workorder",
            "description": "Description",
            "createdAt": datetime.now(timezone.utc),
            "updatedAt": datetime.now(timezone.utc),
            "deleted": False
        }
        
        result = translate_tracos_to_client(workorder)
        
        assert result['status'] == 'ON_HOLD'
        assert result['isOnHold'] is True


class TestFormatDatetime:
    """Tests for datetime formatting function."""
    
    def test_format_datetime_object(self):
        """Test formatting a datetime object."""
        dt = datetime(2025, 11, 1, 10, 0, 0, tzinfo=timezone.utc)
        result = _format_datetime(dt)
        
        assert isinstance(result, str)
        assert "2025-11-01" in result
    
    def test_format_none_returns_current_time(self):
        """Test that None returns current time as ISO string."""
        before = datetime.now(timezone.utc)
        result = _format_datetime(None)
        after = datetime.now(timezone.utc)
        
        assert isinstance(result, str)
        # Should be parseable
        parsed = datetime.fromisoformat(result)
        assert before <= parsed <= after
    
    def test_format_string_passthrough(self):
        """Test that string dates pass through unchanged."""
        date_str = "2025-11-01T10:00:00+00:00"
        result = _format_datetime(date_str)
        
        assert result == date_str


class TestTranslationRoundTrip:
    """Tests for round-trip translation consistency."""
    
    def test_client_to_tracos_to_client_preserves_key_fields(self, sample_client_workorder):
        """Test that translating client → TracOS → client preserves essential fields."""
        tracos = translate_client_to_tracos(sample_client_workorder)
        client = translate_tracos_to_client(tracos)
        
        # Key fields should be preserved
        assert client['orderNo'] == sample_client_workorder['orderNo']
        assert client['summary'] == sample_client_workorder['summary']
        assert client['isDeleted'] == sample_client_workorder['isDeleted']
    
    def test_tracos_to_client_to_tracos_preserves_key_fields(self, sample_tracos_workorder):
        """Test that translating TracOS → client → TracOS preserves essential fields."""
        client = translate_tracos_to_client(sample_tracos_workorder)
        tracos = translate_client_to_tracos(client)
        
        # Key fields should be preserved
        assert tracos['number'] == sample_tracos_workorder['number']
        assert tracos['deleted'] == sample_tracos_workorder['deleted']
        # Status should be equivalent
        assert tracos['status'] == sample_tracos_workorder['status']

