"""
Tests for status mapping between Client and TracOS systems.

These tests verify:
- All status enum mappings work correctly
- Boolean flag fallback works (backward compatibility)
- Priority order is correct (enum > flags)
- Edge cases and unknown statuses are handled
"""

import pytest
from integration.translators.status_mappings import (
    map_client_status_to_tracos,
    map_tracos_status_to_client,
    CLIENT_TO_TRACOS_STATUS,
    TRACOS_TO_CLIENT_STATUS,
)


class TestClientToTracOSStatusMapping:
    """Tests for Client → TracOS status mapping."""
    
    def test_all_enum_mappings(self, client_to_tracos_status_cases):
        """Test all documented status enum mappings."""
        enum_cases = [c for c in client_to_tracos_status_cases if c.get("status")]
        
        for case in enum_cases:
            result = map_client_status_to_tracos(
                status=case["status"],
                flags=case.get("flags")
            )
            assert result == case["expected"], \
                f"Status '{case['status']}' should map to '{case['expected']}', got '{result}'"
    
    def test_flag_based_mapping(self, client_to_tracos_status_cases):
        """Test flag-based status mapping (backward compatibility)."""
        flag_cases = [c for c in client_to_tracos_status_cases 
                      if c.get("status") is None and c.get("flags")]
        
        for case in flag_cases:
            result = map_client_status_to_tracos(
                status=None,
                flags=case["flags"]
            )
            assert result == case["expected"], \
                f"Flags {case['flags']} should map to '{case['expected']}', got '{result}'"
    
    def test_case_insensitivity(self):
        """Test that status matching is case-insensitive."""
        # Lowercase
        assert map_client_status_to_tracos(status="new") == "created"
        # Uppercase
        assert map_client_status_to_tracos(status="NEW") == "created"
        # Mixed case
        assert map_client_status_to_tracos(status="New") == "created"
        assert map_client_status_to_tracos(status="nEw") == "created"
    
    def test_cancelled_both_spellings(self):
        """Test both American and British spellings of cancelled."""
        assert map_client_status_to_tracos(status="CANCELLED") == "cancelled"
        assert map_client_status_to_tracos(status="CANCELED") == "cancelled"
    
    def test_default_when_no_status_or_flags(self):
        """Test default status when neither status nor flags are provided."""
        result = map_client_status_to_tracos(status=None, flags=None)
        assert result == "in_progress"
        
        result = map_client_status_to_tracos(status=None, flags={})
        assert result == "in_progress"
    
    def test_unknown_status_falls_back_to_flags(self):
        """Test that unknown status value falls back to flags."""
        result = map_client_status_to_tracos(
            status="UNKNOWN_STATUS",
            flags={"isDone": True}
        )
        assert result == "completed"
    
    def test_flag_priority_order(self):
        """Test that flags are checked in correct priority order."""
        # isDeleted has highest priority
        result = map_client_status_to_tracos(
            status=None,
            flags={
                "isDeleted": True,
                "isCanceled": True,
                "isDone": True,
                "isOnHold": True,
                "isPending": True
            }
        )
        assert result == "deleted"
        
        # isCanceled is next
        result = map_client_status_to_tracos(
            status=None,
            flags={
                "isDeleted": False,
                "isCanceled": True,
                "isDone": True,
                "isOnHold": True,
                "isPending": True
            }
        )
        assert result == "cancelled"
        
        # isDone is next
        result = map_client_status_to_tracos(
            status=None,
            flags={
                "isDeleted": False,
                "isCanceled": False,
                "isDone": True,
                "isOnHold": True,
                "isPending": True
            }
        )
        assert result == "completed"
    
    def test_status_enum_takes_priority(self):
        """Test that status enum always takes priority over flags."""
        result = map_client_status_to_tracos(
            status="PENDING",
            flags={
                "isDeleted": True,  # This would normally override
                "isDone": True
            }
        )
        assert result == "pending"
    
    def test_empty_string_status_uses_flags(self):
        """Test that empty string status falls back to flags."""
        result = map_client_status_to_tracos(
            status="",
            flags={"isDone": True}
        )
        # Empty string is falsy, so should fall back to flags
        assert result == "completed"


class TestTracOSToClientStatusMapping:
    """Tests for TracOS → Client status mapping."""
    
    def test_all_enum_mappings(self, tracos_to_client_status_cases):
        """Test all documented TracOS → Client status mappings."""
        for case in tracos_to_client_status_cases:
            result = map_tracos_status_to_client(status=case["status"])
            
            assert result["status"] == case["expected_status"], \
                f"Status '{case['status']}' should map to '{case['expected_status']}', got '{result['status']}'"
    
    def test_correct_flags_set(self, tracos_to_client_status_cases):
        """Test that correct boolean flags are set for each status."""
        for case in tracos_to_client_status_cases:
            result = map_tracos_status_to_client(status=case["status"])
            
            for flag_name, expected_value in case["expected_flags"].items():
                actual_value = result["flags"].get(flag_name, False)
                assert actual_value == expected_value, \
                    f"For status '{case['status']}', flag '{flag_name}' should be {expected_value}, got {actual_value}"
    
    def test_case_insensitivity(self):
        """Test that status matching is case-insensitive."""
        # Lowercase
        result = map_tracos_status_to_client(status="completed")
        assert result["status"] == "COMPLETED"
        
        # Uppercase
        result = map_tracos_status_to_client(status="COMPLETED")
        assert result["status"] == "COMPLETED"
        
        # Mixed case
        result = map_tracos_status_to_client(status="Completed")
        assert result["status"] == "COMPLETED"
    
    def test_none_status_returns_none_with_empty_flags(self):
        """Test that None status returns appropriate empty result."""
        result = map_tracos_status_to_client(status=None)
        
        assert result["status"] is None
        # All flags should be False
        for flag_name, flag_value in result["flags"].items():
            assert flag_value is False, f"Flag {flag_name} should be False for None status"
    
    def test_empty_string_status_returns_none(self):
        """Test that empty string status returns None."""
        result = map_tracos_status_to_client(status="")
        
        assert result["status"] is None
    
    def test_unknown_status_returns_none(self):
        """Test that unknown status returns None but keeps default flags."""
        result = map_tracos_status_to_client(status="unknown_status_xyz")
        
        assert result["status"] is None
        # All flags should still be False
        for flag_name, flag_value in result["flags"].items():
            assert flag_value is False
    
    def test_all_flags_present_in_result(self):
        """Test that all expected flags are present in the result."""
        result = map_tracos_status_to_client(status="created")
        
        expected_flags = ["isCanceled", "isDone", "isOnHold", "isPending"]
        for flag in expected_flags:
            assert flag in result["flags"], f"Missing flag: {flag}"
    
    def test_result_structure(self):
        """Test that result has correct structure."""
        result = map_tracos_status_to_client(status="completed")
        
        assert "status" in result
        assert "flags" in result
        assert isinstance(result["flags"], dict)


class TestMappingConsistency:
    """Tests for consistency between mapping dictionaries."""
    
    def test_bidirectional_mapping_consistency(self):
        """Test that CLIENT_TO_TRACOS and TRACOS_TO_CLIENT are inverse mappings."""
        for client_status, tracos_status in CLIENT_TO_TRACOS_STATUS.items():
            # Skip alternate spellings
            if client_status == "CANCELED":
                continue
                
            reverse = TRACOS_TO_CLIENT_STATUS.get(tracos_status)
            assert reverse is not None, \
                f"TracOS status '{tracos_status}' has no reverse mapping"
    
    def test_all_tracos_statuses_have_reverse(self):
        """Test that all TracOS statuses can be mapped back to client."""
        for tracos_status in TRACOS_TO_CLIENT_STATUS.keys():
            client_status = TRACOS_TO_CLIENT_STATUS[tracos_status]
            assert client_status in CLIENT_TO_TRACOS_STATUS, \
                f"Client status '{client_status}' from TracOS '{tracos_status}' not in forward mapping"
    
    def test_round_trip_client_to_tracos_to_client(self):
        """Test round-trip mapping preserves status (where applicable)."""
        # These should round-trip cleanly
        round_trip_statuses = ["NEW", "PENDING", "IN_PROGRESS", "ON_HOLD", "COMPLETED", "DELETED"]
        
        for client_status in round_trip_statuses:
            tracos_status = map_client_status_to_tracos(status=client_status)
            result = map_tracos_status_to_client(status=tracos_status)
            
            assert result["status"] == client_status, \
                f"Round trip failed: {client_status} → {tracos_status} → {result['status']}"
    
    def test_cancelled_round_trip(self):
        """Test that CANCELLED round-trips (not CANCELED)."""
        tracos_status = map_client_status_to_tracos(status="CANCELLED")
        result = map_tracos_status_to_client(status=tracos_status)
        
        # Should return canonical spelling CANCELLED
        assert result["status"] == "CANCELLED"


class TestEdgeCases:
    """Tests for edge cases and potential vulnerabilities."""
    
    def test_whitespace_in_status(self):
        """Test handling of status with whitespace."""
        # Leading/trailing whitespace - should not match
        result = map_client_status_to_tracos(status=" NEW ", flags=None)
        # Should fall through to default since " NEW " != "NEW"
        assert result == "in_progress"
    
    def test_special_characters_in_status(self):
        """Test handling of special characters in status."""
        result = map_client_status_to_tracos(status="NEW\n", flags=None)
        assert result == "in_progress"  # Should not match
    
    def test_unicode_in_status(self):
        """Test handling of unicode characters in status."""
        result = map_client_status_to_tracos(status="NÉW", flags=None)
        assert result == "in_progress"  # Should not match
    
    def test_flags_with_none_values(self):
        """Test handling of flags dictionary with None values."""
        result = map_client_status_to_tracos(
            status=None,
            flags={
                "isDone": None,
                "isDeleted": None,
                "isCanceled": None,
                "isOnHold": None,
                "isPending": None
            }
        )
        # None is falsy, so should return default
        assert result == "in_progress"
    
    def test_extra_flags_ignored(self):
        """Test that extra flags are ignored."""
        result = map_client_status_to_tracos(
            status=None,
            flags={
                "isDone": True,
                "isDeleted": False,
                "unknownFlag": True,
                "anotherUnknown": "value"
            }
        )
        assert result == "completed"
    
    def test_integer_status_value(self):
        """Test handling of non-string status value."""
        # This tests type safety - in practice status should be string
        try:
            result = map_client_status_to_tracos(status=123, flags=None)
            # Should handle gracefully, likely return default
            assert result == "in_progress"
        except (TypeError, AttributeError):
            # Exception is also acceptable for wrong type
            pass
    
    def test_very_long_status_string(self):
        """Test handling of very long status string (potential DoS)."""
        long_status = "A" * 10000
        result = map_client_status_to_tracos(status=long_status, flags=None)
        # Should not hang, should return default
        assert result == "in_progress"

