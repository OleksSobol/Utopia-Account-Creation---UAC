"""
Failure tracking system for failed customer creation attempts.

This module handles:
- Recording failed order references with failure details
- Saving/loading failure data to/from JSON file
- Managing failure records (add, remove, list)
"""

import json
import os
import logging
from datetime import datetime
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

class FailureTracker:
    """
    Manages tracking of failed customer creation attempts
    """
    
    def __init__(self, failure_file_path: str = "failed_orders.json"):
        """
        Initialize failure tracker
        
        Args:
            failure_file_path: Path to JSON file for storing failure data
        """
        self.failure_file_path = failure_file_path
        self._ensure_file_exists()
    
    def _ensure_file_exists(self):
        """Create failure file if it doesn't exist"""
        if not os.path.exists(self.failure_file_path):
            self._save_failures({})
            logger.info(f"Created new failure tracking file: {self.failure_file_path}")
    
    def _load_failures(self) -> Dict:
        """
        Load failure data from JSON file
        
        Returns:
            Dictionary of failure data
        """
        try:
            with open(self.failure_file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            logger.error(f"Error loading failure data: {e}")
            return {}
    
    def _save_failures(self, failures: Dict):
        """
        Save failure data to JSON file
        
        Args:
            failures: Dictionary of failure data to save
        """
        try:
            with open(self.failure_file_path, 'w', encoding='utf-8') as f:
                json.dump(failures, f, indent=2, ensure_ascii=False)
            logger.debug(f"Saved failure data to {self.failure_file_path}")
        except Exception as e:
            logger.error(f"Error saving failure data: {e}")
    
    def _generate_unique_orderref(self) -> str:
        """
        Generate a unique orderref for failures without an order reference
        
        Returns:
            Unique identifier string
        """
        # Use timestamp + short UUID for uniqueness
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        short_uuid = str(uuid.uuid4())[:8]
        return f"UNKNOWN_{timestamp}_{short_uuid}"
    
    def record_failure(self, orderref: str, error_message: str, failure_type: str = "customer_creation", 
                      customer_data: Optional[Dict] = None):
        """
        Record a new failure
        
        Args:
            orderref: Order reference that failed
            error_message: Description of what went wrong
            failure_type: Type of failure (customer_creation, service_plan, etc.)
            customer_data: Optional customer data for debugging
        """
        
         # Generate unique orderref if empty or None
        original_orderref = orderref
        if not orderref or not orderref.strip():
            orderref = self._generate_unique_orderref()
            logger.warning(f"No orderref provided, generated: {orderref}")
       
        failures = self._load_failures()
        
        failure_record = {
            "orderref": orderref,
            "error_message": error_message,
            "failure_type": failure_type,
            "timestamp": datetime.now().isoformat(),
            "customer_data": customer_data or {},
            "retry_count": 0,
            "resolved": False
        }
        
        # If orderref already exists, update it (but increment retry count)
        if orderref in failures:
            failure_record["retry_count"] = failures[orderref].get("retry_count", 0) + 1
            failure_record["first_failure"] = failures[orderref].get("timestamp")
            logger.warning(f"Recording repeated failure for orderref {orderref} (retry #{failure_record['retry_count']})")
        else:
            failure_record["first_failure"] = failure_record["timestamp"]
            logger.info(f"Recording new failure for orderref {orderref}")
        
        failures[orderref] = failure_record
        self._save_failures(failures)
        
        logger.error(f"Failure recorded - OrderRef: {orderref}, Type: {failure_type}, Error: {error_message}")
    
    def get_failures(self, include_resolved: bool = False) -> Dict:
        """
        Get all failure records
        
        Args:
            include_resolved: Whether to include resolved failures
            
        Returns:
            Dictionary of failure records
        """
        failures = self._load_failures()
        
        if not include_resolved:
            # Filter out resolved failures
            failures = {k: v for k, v in failures.items() if not v.get("resolved", False)}
        
        return failures
    
    def get_failure_list(self, include_resolved: bool = False) -> List[Dict]:
        """
        Get failure records as a list sorted by timestamp (newest first)
        
        Args:
            include_resolved: Whether to include resolved failures
            
        Returns:
            List of failure records
        """
        failures = self.get_failures(include_resolved)
        
        # Convert to list and sort by timestamp (newest first)
        failure_list = list(failures.values())
        failure_list.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
        
        return failure_list
    
    def remove_failure(self, orderref: str) -> bool:
        """
        Remove a failure record
        
        Args:
            orderref: Order reference to remove
            
        Returns:
            True if removed, False if not found
        """
        failures = self._load_failures()
        
        if orderref in failures:
            del failures[orderref]
            self._save_failures(failures)
            logger.info(f"Removed failure record for orderref: {orderref}")
            return True
        else:
            logger.warning(f"Attempted to remove non-existent failure record: {orderref}")
            return False
    
    def mark_resolved(self, orderref: str, resolution_note: str = "") -> bool:
        """
        Mark a failure as resolved (instead of deleting)
        
        Args:
            orderref: Order reference to mark as resolved
            resolution_note: Optional note about how it was resolved
            
        Returns:
            True if marked as resolved, False if not found
        """
        failures = self._load_failures()
        
        if orderref in failures:
            failures[orderref]["resolved"] = True
            failures[orderref]["resolved_timestamp"] = datetime.now().isoformat()
            failures[orderref]["resolution_note"] = resolution_note
            self._save_failures(failures)
            logger.info(f"Marked failure as resolved for orderref: {orderref}")
            return True
        else:
            logger.warning(f"Attempted to mark non-existent failure as resolved: {orderref}")
            return False
    
    def get_failure_stats(self) -> Dict:
        """
        Get statistics about failures
        
        Returns:
            Dictionary with failure statistics
        """
        failures = self._load_failures()
        
        total_failures = len(failures)
        unresolved_failures = len([f for f in failures.values() if not f.get("resolved", False)])
        resolved_failures = total_failures - unresolved_failures
        
        # Count by failure type
        failure_types = {}
        for failure in failures.values():
            failure_type = failure.get("failure_type", "unknown")
            failure_types[failure_type] = failure_types.get(failure_type, 0) + 1
        
        # Count retries
        retries = sum(f.get("retry_count", 0) for f in failures.values())
        
        return {
            "total_failures": total_failures,
            "unresolved_failures": unresolved_failures,
            "resolved_failures": resolved_failures,
            "failure_types": failure_types,
            "total_retries": retries
        }
    
    def cleanup_old_resolved(self, days_old: int = 30) -> int:
        """
        Remove resolved failures older than specified days
        
        Args:
            days_old: Remove resolved failures older than this many days
            
        Returns:
            Number of records removed
        """
        from datetime import timedelta
        
        failures = self._load_failures()
        cutoff_date = datetime.now() - timedelta(days=days_old)
        
        removed_count = 0
        to_remove = []
        
        for orderref, failure in failures.items():
            if failure.get("resolved", False):
                resolved_timestamp = failure.get("resolved_timestamp", failure.get("timestamp"))
                if resolved_timestamp:
                    try:
                        resolved_date = datetime.fromisoformat(resolved_timestamp)
                        if resolved_date < cutoff_date:
                            to_remove.append(orderref)
                    except ValueError:
                        # Invalid timestamp format, skip
                        continue
        
        for orderref in to_remove:
            del failures[orderref]
            removed_count += 1
        
        if removed_count > 0:
            self._save_failures(failures)
            logger.info(f"Cleaned up {removed_count} old resolved failures")
        
        return removed_count