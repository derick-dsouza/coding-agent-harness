"""
Tests for Linear Batch Update Helper

Verifies batch operations work correctly and provide expected efficiency gains.
"""

import pytest
import json
from unittest.mock import Mock, patch, MagicMock
from linear_batch_helper import (
    batch_update_issues,
    batch_add_labels,
    batch_update_status,
    get_batch_stats
)


class TestBatchUpdateIssues:
    """Test the main batch update function."""
    
    @patch('task_management.linear_adapter.LinearAdapter')
    def test_batch_update_success(self, mock_adapter_class):
        """Test successful batch update."""
        # Setup mock
        mock_adapter = Mock()
        mock_adapter_class.return_value = mock_adapter
        
        # Create mock issue results
        mock_issue1 = Mock()
        mock_issue1.id = "ISS-001"
        mock_issue1.title = "Feature 1"
        mock_issue1.status = "DONE"
        mock_issue1.labels = [Mock(name="audited")]
        
        mock_issue2 = Mock()
        mock_issue2.id = "ISS-002"
        mock_issue2.title = "Feature 2"
        mock_issue2.status = "DONE"
        mock_issue2.labels = [Mock(name="audited")]
        
        mock_adapter.update_issues_batch.return_value = [mock_issue1, mock_issue2]
        
        # Test
        updates = [
            {"issue_id": "ISS-001", "labels": ["audited"]},
            {"issue_id": "ISS-002", "labels": ["audited"]}
        ]
        
        result = batch_update_issues(updates)
        
        # Verify
        assert result["success"] is True
        assert result["updated_count"] == 2
        assert len(result["results"]) == 2
        assert result["results"][0]["id"] == "ISS-001"
        assert result["results"][1]["id"] == "ISS-002"
        assert len(result["errors"]) == 0
        
        # Verify adapter was called correctly
        mock_adapter.update_issues_batch.assert_called_once_with(updates, batch_size=20)
    
    @patch('task_management.linear_adapter.LinearAdapter')
    def test_batch_update_with_custom_batch_size(self, mock_adapter_class):
        """Test batch update with custom batch size."""
        mock_adapter = Mock()
        mock_adapter_class.return_value = mock_adapter
        mock_adapter.update_issues_batch.return_value = []
        
        updates = [{"issue_id": "ISS-001", "status": "DONE"}]
        batch_update_issues(updates, batch_size=10)
        
        mock_adapter.update_issues_batch.assert_called_once_with(updates, batch_size=10)
    
    @patch('task_management.linear_adapter.LinearAdapter')
    def test_batch_update_error_handling(self, mock_adapter_class):
        """Test error handling in batch update."""
        mock_adapter = Mock()
        mock_adapter_class.return_value = mock_adapter
        mock_adapter.update_issues_batch.side_effect = Exception("API Error")
        
        updates = [{"issue_id": "ISS-001", "status": "DONE"}]
        result = batch_update_issues(updates)
        
        assert result["success"] is False
        assert result["updated_count"] == 0
        assert len(result["results"]) == 0
        assert "API Error" in result["errors"][0]


class TestBatchAddLabels:
    """Test the batch add labels convenience function."""
    
    @patch('linear_batch_helper.batch_update_issues')
    def test_batch_add_labels(self, mock_batch_update):
        """Test adding same labels to multiple issues."""
        mock_batch_update.return_value = {
            "success": True,
            "updated_count": 3,
            "results": [],
            "errors": []
        }
        
        issue_ids = ["ISS-001", "ISS-002", "ISS-003"]
        label_ids = ["label-audited", "label-verified"]
        
        result = batch_add_labels(issue_ids, label_ids)
        
        # Verify it calls batch_update_issues with correct format
        expected_updates = [
            {"issue_id": "ISS-001", "labels": ["label-audited", "label-verified"]},
            {"issue_id": "ISS-002", "labels": ["label-audited", "label-verified"]},
            {"issue_id": "ISS-003", "labels": ["label-audited", "label-verified"]}
        ]
        mock_batch_update.assert_called_once_with(expected_updates)
        
        assert result["success"] is True
        assert result["updated_count"] == 3


class TestBatchUpdateStatus:
    """Test the batch update status convenience function."""
    
    @patch('linear_batch_helper.batch_update_issues')
    def test_batch_update_status(self, mock_batch_update):
        """Test updating status for multiple issues."""
        mock_batch_update.return_value = {
            "success": True,
            "updated_count": 5,
            "results": [],
            "errors": []
        }
        
        issue_ids = ["ISS-001", "ISS-002", "ISS-003", "ISS-004", "ISS-005"]
        
        result = batch_update_status(issue_ids, "DONE")
        
        # Verify it calls batch_update_issues with correct format
        expected_updates = [
            {"issue_id": "ISS-001", "status": "DONE"},
            {"issue_id": "ISS-002", "status": "DONE"},
            {"issue_id": "ISS-003", "status": "DONE"},
            {"issue_id": "ISS-004", "status": "DONE"},
            {"issue_id": "ISS-005", "status": "DONE"}
        ]
        mock_batch_update.assert_called_once_with(expected_updates)
        
        assert result["success"] is True
        assert result["updated_count"] == 5


class TestGetBatchStats:
    """Test batch statistics function."""
    
    def test_get_batch_stats(self):
        """Test getting batch operation statistics."""
        stats = get_batch_stats()
        
        assert "batch_recommendation" in stats
        assert "max_batch_size" in stats
        assert "typical_savings" in stats
        assert stats["max_batch_size"] == 20


class TestRealWorldScenarios:
    """Test realistic batch operation scenarios."""
    
    @patch('task_management.linear_adapter.LinearAdapter')
    def test_audit_session_scenario(self, mock_adapter_class):
        """Test typical audit session with 20 features."""
        mock_adapter = Mock()
        mock_adapter_class.return_value = mock_adapter
        
        # Simulate 20 passing features
        mock_issues = []
        for i in range(20):
            mock_issue = Mock()
            mock_issue.id = f"ISS-{i:03d}"
            mock_issue.title = f"Feature {i}"
            mock_issue.status = "DONE"
            mock_issue.labels = [Mock(name="audited")]
            mock_issues.append(mock_issue)
        
        mock_adapter.update_issues_batch.return_value = mock_issues
        
        # Prepare batch update for all 20 features
        updates = [
            {"issue_id": f"ISS-{i:03d}", "labels": ["audited"]}
            for i in range(20)
        ]
        
        result = batch_update_issues(updates)
        
        # Verify efficiency
        assert result["success"] is True
        assert result["updated_count"] == 20
        
        # Verify only ONE call to adapter (not 20!)
        assert mock_adapter.update_issues_batch.call_count == 1
    
    @patch('linear_batch_helper.batch_update_issues')
    def test_legacy_labeling_scenario(self, mock_batch_update):
        """Test labeling legacy issues without audit labels."""
        mock_batch_update.return_value = {
            "success": True,
            "updated_count": 15,
            "results": [],
            "errors": []
        }
        
        # 15 legacy issues need labeling
        legacy_issue_ids = [f"ISS-{i:03d}" for i in range(100, 115)]
        awaiting_audit_label = "label-awaiting-audit"
        
        result = batch_add_labels(legacy_issue_ids, [awaiting_audit_label])
        
        # One batch call for 15 issues (not 15 individual calls!)
        assert mock_batch_update.call_count == 1
        assert result["updated_count"] == 15


class TestBatchVsIndividualComparison:
    """Compare batch vs individual update efficiency."""
    
    @patch('task_management.linear_adapter.LinearAdapter')
    def test_efficiency_comparison(self, mock_adapter_class):
        """Document the efficiency gains from batching."""
        mock_adapter = Mock()
        mock_adapter_class.return_value = mock_adapter
        
        # Mock successful batch update
        mock_issues = [Mock(id=f"ISS-{i}", title=f"F{i}", status="DONE", labels=[]) 
                       for i in range(10)]
        mock_adapter.update_issues_batch.return_value = mock_issues
        
        # Batch approach: 10 issues in 1 call
        updates = [{"issue_id": f"ISS-{i}", "status": "DONE"} for i in range(10)]
        result = batch_update_issues(updates)
        
        batch_api_calls = mock_adapter.update_issues_batch.call_count
        
        # Individual approach would be: 10 issues = 10 separate update_issue calls
        individual_api_calls = 10
        
        # Calculate savings
        savings_percent = ((individual_api_calls - batch_api_calls) / individual_api_calls) * 100
        
        assert batch_api_calls == 1
        assert savings_percent == 90.0  # 90% reduction!
        
        print(f"""
        Efficiency Comparison:
        ----------------------
        Individual updates: {individual_api_calls} API calls
        Batch update: {batch_api_calls} API call
        Savings: {savings_percent}%
        
        For a typical audit session (20 features):
        - Individual: 20 API calls
        - Batch: 1 API call
        - Reduction: 95%!
        """)


def test_import_in_agent_context():
    """Test that imports work from agent context."""
    # This simulates how agents will use the helper
    try:
        from linear_batch_helper import batch_update_issues, batch_add_labels
        assert callable(batch_update_issues)
        assert callable(batch_add_labels)
    except ImportError as e:
        pytest.fail(f"Import failed: {e}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
