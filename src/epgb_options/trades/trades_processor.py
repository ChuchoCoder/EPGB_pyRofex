"""
Trades Processor Module

Processes raw execution dicts into validated pandas DataFrame.
"""

from datetime import datetime
from typing import Dict, List

import pandas as pd

from ..utils.logging import get_logger

logger = get_logger(__name__)


class TradesProcessor:
    """Processes executions into DataFrame."""
    
    def process_executions(self, executions: List[Dict]) -> pd.DataFrame:
        """
        Convert executions to DataFrame with validation.
        
        Args:
            executions: List of execution dicts
            
        Returns:
            Validated DataFrame with composite index
        """
        if not executions:
            logger.warning("No executions to process")
            return pd.DataFrame()
        
        try:
            # Convert to DataFrame
            df = pd.DataFrame(executions)
            
            # Parse timestamps
            df['TimestampUTC'] = pd.to_datetime(df['TimestampUTC'], utc=True)
            
            # Data type conversions
            numeric_cols = ['Quantity', 'Price', 'FilledQty']
            for col in numeric_cols:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors='coerce')
            
            # Optional numeric columns
            if 'LastQty' in df.columns:
                df['LastQty'] = pd.to_numeric(df['LastQty'], errors='coerce')
            if 'LastPx' in df.columns:
                df['LastPx'] = pd.to_numeric(df['LastPx'], errors='coerce')
            
            # CRITICAL: Ensure index columns are strings for consistent comparison
            # This prevents type mismatches during merge operations
            index_cols = ['ExecutionID', 'OrderID', 'Account']
            for col in index_cols:
                if col in df.columns:
                    df[col] = df[col].astype(str)
            
            # Sort by timestamp (handle out-of-order events)
            df.sort_values('TimestampUTC', inplace=True)
            
            # Validate required columns exist
            required_cols = ['ExecutionID', 'OrderID', 'Account', 'Symbol', 
                           'Side', 'Quantity', 'FilledQty', 'TimestampUTC', 
                           'Status', 'ExecutionType', 'Source']
            missing_cols = [col for col in required_cols if col not in df.columns]
            if missing_cols:
                logger.error(f"Missing required columns: {missing_cols}")
                return pd.DataFrame()
            
            # Check for duplicates BEFORE setting index
            duplicates_mask = df.duplicated(subset=['ExecutionID', 'OrderID', 'Account'], keep=False)
            if duplicates_mask.any():
                num_duplicates = duplicates_mask.sum()
                logger.warning(f"Found {num_duplicates} duplicate executions from broker - keeping latest by timestamp")
                # Keep the latest execution by timestamp for each ExecutionID+OrderID+Account
                df = df.sort_values('TimestampUTC').drop_duplicates(
                    subset=['ExecutionID', 'OrderID', 'Account'], 
                    keep='last'  # Keep the most recent
                )
                logger.info(f"After deduplication: {len(df)} unique executions")
            
            # Set composite index
            df.set_index(['ExecutionID', 'OrderID', 'Account'], inplace=True)
            
            logger.debug(f"Processed {len(df)} executions")
            return df
            
        except Exception as e:
            logger.error(f"Error processing executions: {e}", exc_info=True)
            return pd.DataFrame()
    
    def validate_execution(self, execution: Dict) -> bool:
        """
        Validate a single execution dict.
        
        Args:
            execution: Execution dict to validate
            
        Returns:
            True if valid, False otherwise
        """
        # Check required fields
        required_fields = ['ExecutionID', 'OrderID', 'Account', 'Symbol', 
                          'Side', 'Quantity', 'FilledQty', 'Status']
        
        for field in required_fields:
            if field not in execution or not execution[field]:
                logger.debug(f"Validation failed: missing {field}")
                return False
        
        # Validate enums
        valid_sides = ['BUY', 'SELL']
        if execution['Side'] not in valid_sides:
            logger.debug(f"Invalid Side: {execution['Side']}")
            return False
        
        valid_statuses = ['NEW', 'PARTIALLY_FILLED', 'FILLED', 'CANCELED', 'REJECTED', 'EXPIRED']
        if execution['Status'] not in valid_statuses:
            logger.debug(f"Invalid Status: {execution['Status']}")
            return False
        
        # Validate numeric ranges
        try:
            qty = float(execution['Quantity'])
            filled_qty = float(execution['FilledQty'])
            
            if qty <= 0:
                logger.debug(f"Invalid Quantity: {qty}")
                return False
            
            if filled_qty < 0 or filled_qty > qty:
                logger.debug(f"Invalid FilledQty: {filled_qty} (Quantity: {qty})")
                return False
                
        except (ValueError, TypeError) as e:
            logger.debug(f"Numeric validation failed: {e}")
            return False
        
        return True
