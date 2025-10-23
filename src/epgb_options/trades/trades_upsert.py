"""
Trades Upsert Module

Idempotent upsert of executions to Excel Trades sheet.
MUST use bulk range updates per Constitution II.
"""

from datetime import datetime
from typing import Dict

import pandas as pd
import xlwings as xw

from ..config.excel_config import EXCEL_SHEET_TRADES, TRADES_COLUMNS
from ..utils.logging import get_logger

logger = get_logger(__name__)


class TradesUpserter:
    """Handles upsert operations for Trades sheet."""
    
    def __init__(self, workbook: xw.Book):
        """
        Initialize upserter.
        
        Args:
            workbook: xlwings Workbook object
        """
        self.workbook = workbook
        self.sheet = self._get_or_create_trades_sheet()
    
    def upsert_executions(self, new_executions_df: pd.DataFrame) -> Dict[str, int]:
        """
        Idempotent upsert of executions to Trades sheet.
        Uses BULK RANGE UPDATE (single xlwings write operation).
        
        Args:
            new_executions_df: DataFrame with executions (composite index set)
            
        Returns:
            Stats dict: {'inserted': int, 'updated': int, 'unchanged': int}
        """
        if new_executions_df.empty:
            logger.info("No executions to upsert")
            return {'inserted': 0, 'updated': 0, 'unchanged': 0}
        
        try:
            # 1. Read existing trades (BULK READ)
            existing_df = self._read_existing_trades()
            
            # 2. Merge new with existing (pandas merge)
            merged = self._merge_executions(existing_df, new_executions_df)
            
            # 3. Build final DataFrame with audit columns
            final_df = self._build_final_with_audit(merged)
            
            # 4. CRITICAL: BULK WRITE to Excel (single operation)
            self._write_bulk_to_excel(final_df)
            
            # 5. Calculate stats
            stats = self._calculate_stats(merged)
            logger.info(f"Upsert complete: {stats}")
            return stats
            
        except Exception as e:
            logger.error(f"Error in upsert_executions: {e}", exc_info=True)
            return {'inserted': 0, 'updated': 0, 'unchanged': 0, 'errors': 1}
    
    def _read_existing_trades(self) -> pd.DataFrame:
        """Read existing Trades sheet data (bulk read)."""
        try:
            # Read header row first to determine actual columns in Excel
            header_range = self.sheet.range('A1').expand('right')
            header_value = header_range.value
            
            # Handle single header case
            if not isinstance(header_value, (list, tuple)):
                existing_headers = [header_value] if header_value else []
            else:
                existing_headers = [h for h in header_value if h is not None]
            
            # Check if sheet has no headers or is empty
            if not existing_headers:
                empty_df = pd.DataFrame(columns=list(TRADES_COLUMNS.keys()))
                logger.debug("Trades sheet has no headers, starting fresh")
                return empty_df
            
            # Determine the last column letter based on existing headers
            num_existing_cols = len(existing_headers)
            existing_col_letters = list(TRADES_COLUMNS.values())[:num_existing_cols]
            last_existing_col = existing_col_letters[-1] if existing_col_letters else 'A'
            
            # Read data range (from A2 to last existing column)
            # Use expand('down') to handle blanks properly
            first_data_cell = self.sheet.range('A2')
            if first_data_cell.value is None:
                # No data rows
                empty_df = pd.DataFrame(columns=list(TRADES_COLUMNS.keys()))
                logger.debug("Trades sheet is empty, starting fresh")
                return empty_df
            
            # Read the data range with specific columns
            data_range = self.sheet.range(f'A2:{last_existing_col}2').expand('down')
            raw_data = data_range.value
            
            # Check if data is empty
            if raw_data is None or (isinstance(raw_data, list) and len(raw_data) == 0):
                empty_df = pd.DataFrame(columns=list(TRADES_COLUMNS.keys()))
                logger.debug("Trades sheet is empty, starting fresh")
                return empty_df
            
            # Handle single row case (xlwings returns list, not list of lists)
            if not isinstance(raw_data[0], (list, tuple)):
                raw_data = [raw_data]
            
            # Create DataFrame with existing headers
            df = pd.DataFrame(raw_data, columns=existing_headers)
            
            # Add missing columns with None values if the sheet has fewer columns than expected
            expected_columns = list(TRADES_COLUMNS.keys())
            for col in expected_columns:
                if col not in df.columns:
                    df[col] = None
                    logger.debug(f"Added missing column '{col}' with None values")
            
            # Ensure column order matches expected order
            df = df[expected_columns]
            
            # Convert data types
            if not df.empty:
                # Convert timestamps
                if 'TimestampUTC' in df.columns:
                    df['TimestampUTC'] = pd.to_datetime(df['TimestampUTC'], errors='coerce')
                if 'PreviousTimestampUTC' in df.columns:
                    df['PreviousTimestampUTC'] = pd.to_datetime(df['PreviousTimestampUTC'], errors='coerce')
                
                # Convert numeric columns
                numeric_cols = ['Quantity', 'Price', 'FilledQty', 'PreviousFilledQty', 'UpdateCount']
                for col in numeric_cols:
                    if col in df.columns:
                        df[col] = pd.to_numeric(df[col], errors='coerce')
                
                # Convert boolean
                if 'Superseded' in df.columns:
                    df['Superseded'] = df['Superseded'].fillna(False).astype(bool)
                
                # Set composite index
                df.set_index(['ExecutionID', 'OrderID', 'Account'], inplace=True)
            
            logger.debug(f"Read {len(df)} existing trades")
            return df
            
        except Exception as e:
            logger.error(f"Error reading existing trades: {e}", exc_info=True)
            # Return empty DataFrame on error
            return pd.DataFrame(columns=list(TRADES_COLUMNS.keys()))
    
    def _merge_executions(self, existing: pd.DataFrame, new: pd.DataFrame) -> pd.DataFrame:
        """
        Merge existing and new executions with indicator.
        
        Args:
            existing: Existing executions from Excel
            new: New executions to upsert
            
        Returns:
            Merged DataFrame with _merge indicator
        """
        # Ensure both DataFrames have the same index
        if existing.empty:
            # No existing data, all new records are inserts
            new_copy = new.copy()
            new_copy['_merge'] = 'right_only'
            return new_copy
        
        if new.empty:
            # No new data
            existing_copy = existing.copy()
            existing_copy['_merge'] = 'left_only'
            return existing_copy
        
        # Merge with indicator to identify inserts/updates
        merged = existing.merge(
            new,
            how='outer',
            left_index=True,
            right_index=True,
            indicator=True,
            suffixes=('_old', '_new'),
            sort=False  # Suppress unorderable values warning
        )
        
        return merged
    
    def _build_final_with_audit(self, merged: pd.DataFrame) -> pd.DataFrame:
        """
        Build final DataFrame with audit columns populated.
        
        Args:
            merged: Merged DataFrame from _merge_executions
            
        Returns:
            Final DataFrame ready for Excel write
        """
        if merged.empty:
            return pd.DataFrame(columns=list(TRADES_COLUMNS.keys()))
        
        final_rows = []
        
        for idx, row in merged.iterrows():
            merge_type = row['_merge']
            
            if merge_type == 'right_only':
                # New insert - take all _new values, initialize audit columns
                final_row = {}
                for col in TRADES_COLUMNS.keys():
                    if col in ['PreviousFilledQty', 'PreviousTimestampUTC', 'CancelReason']:
                        final_row[col] = None
                    elif col == 'Superseded':
                        final_row[col] = False
                    elif col == 'UpdateCount':
                        final_row[col] = 0
                    else:
                        # Get from new data
                        new_col = f"{col}_new" if f"{col}_new" in row.index else col
                        final_row[col] = row.get(new_col, row.get(col))
                
            elif merge_type == 'both':
                # Update - merge old and new, populate audit columns
                final_row = {}
                
                # Get old and new filled quantities for audit
                old_filled_qty = row.get('FilledQty_old')
                new_filled_qty = row.get('FilledQty_new')
                old_timestamp = row.get('TimestampUTC_old')
                new_status = row.get('Status_new', row.get('Status_old'))
                
                # Use new values for primary columns
                for col in TRADES_COLUMNS.keys():
                    if col in ['PreviousFilledQty', 'PreviousTimestampUTC', 'Superseded', 'CancelReason', 'UpdateCount']:
                        continue  # Handle separately
                    
                    new_col = f"{col}_new" if f"{col}_new" in row.index else col
                    final_row[col] = row.get(new_col, row.get(f"{col}_old", row.get(col)))
                
                # Populate audit columns
                if pd.notna(old_filled_qty) and pd.notna(new_filled_qty) and old_filled_qty != new_filled_qty:
                    final_row['PreviousFilledQty'] = old_filled_qty
                    final_row['PreviousTimestampUTC'] = old_timestamp
                    final_row['Superseded'] = True
                    old_update_count = row.get('UpdateCount_old', 0)
                    final_row['UpdateCount'] = (old_update_count or 0) + 1
                else:
                    # No change in filled qty, preserve old audit data
                    final_row['PreviousFilledQty'] = row.get('PreviousFilledQty_old')
                    final_row['PreviousTimestampUTC'] = row.get('PreviousTimestampUTC_old')
                    final_row['Superseded'] = row.get('Superseded_old', False)
                    final_row['UpdateCount'] = row.get('UpdateCount_old', 0)
                
                # Handle cancellations
                if new_status == 'CANCELED':
                    final_row['CancelReason'] = row.get('CancelReason_new', 'BROKER_CANCELED')
                    final_row['Superseded'] = True
                else:
                    final_row['CancelReason'] = row.get('CancelReason_old', '')
                
            else:  # left_only
                # Existing row with no update - preserve as is
                final_row = {}
                for col in TRADES_COLUMNS.keys():
                    old_col = f"{col}_old" if f"{col}_old" in row.index else col
                    final_row[col] = row.get(old_col, row.get(col))
            
            # Add index values back
            final_row['ExecutionID'] = idx[0]
            final_row['OrderID'] = idx[1]
            final_row['Account'] = idx[2]
            
            final_rows.append(final_row)
        
        # Create final DataFrame
        final_df = pd.DataFrame(final_rows)
        
        # Ensure column order matches TRADES_COLUMNS
        column_order = list(TRADES_COLUMNS.keys())
        final_df = final_df[column_order]
        
        return final_df
    
    def _write_bulk_to_excel(self, df: pd.DataFrame):
        """
        CRITICAL: Bulk write entire DataFrame to Excel in SINGLE operation.
        Per Constitution II, individual cell writes are PROHIBITED.
        
        Args:
            df: Final DataFrame to write
        """
        try:
            if df.empty:
                logger.warning("No data to write to Excel")
                return
            
            # Convert DataFrame to 2D list for xlwings
            # Handle NaT and NaN values
            data = []
            for _, row in df.iterrows():
                row_data = []
                for val in row:
                    if pd.isna(val):
                        row_data.append(None)
                    elif isinstance(val, pd.Timestamp):
                        row_data.append(val.to_pydatetime())
                    else:
                        row_data.append(val)
                data.append(row_data)
            
            # Calculate range
            num_rows = len(data)
            num_cols = len(TRADES_COLUMNS)
            last_col_letter = list(TRADES_COLUMNS.values())[-1]  # 'Q'
            end_row = num_rows + 1  # +1 for header row
            
            # Clear existing data first (from row 2 downward)
            # Get max row to clear old data
            used_range = self.sheet.used_range
            if used_range.last_cell.row > 1:
                clear_range = f'A2:{last_col_letter}{used_range.last_cell.row}'
                self.sheet.range(clear_range).clear_contents()
            
            # SINGLE BULK WRITE
            target_range = f'A2:{last_col_letter}{end_row}'
            self.sheet.range(target_range).value = data
            
            logger.info(f"✅ Bulk write: {num_rows} rows to Excel ({target_range})")
            
        except Exception as e:
            logger.error(f"Error in bulk write: {e}", exc_info=True)
            raise
    
    def _calculate_stats(self, merged: pd.DataFrame) -> Dict[str, int]:
        """
        Calculate upsert statistics from merged DataFrame.
        
        Args:
            merged: Merged DataFrame with _merge indicator
            
        Returns:
            Stats dict with counts
        """
        if merged.empty or '_merge' not in merged.columns:
            return {'inserted': 0, 'updated': 0, 'unchanged': 0}
        
        stats = {
            'inserted': int((merged['_merge'] == 'right_only').sum()),
            'updated': int((merged['_merge'] == 'both').sum()),
            'unchanged': int((merged['_merge'] == 'left_only').sum())
        }
        
        return stats
    
    def _get_or_create_trades_sheet(self) -> xw.Sheet:
        """Get or create Trades sheet in workbook."""
        try:
            sheet = self.workbook.sheets[EXCEL_SHEET_TRADES]
            logger.debug(f"Trades sheet '{EXCEL_SHEET_TRADES}' found")
        except Exception:
            # Create sheet
            sheet = self.workbook.sheets.add(EXCEL_SHEET_TRADES)
            self._create_headers(sheet)
            logger.info(f"Created new Trades sheet: '{EXCEL_SHEET_TRADES}'")
        
        return sheet
    
    def _create_headers(self, sheet: xw.Sheet):
        """Create header row in new Trades sheet."""
        headers = list(TRADES_COLUMNS.keys())
        sheet.range('A1').value = headers
        sheet.range(f'A1:{list(TRADES_COLUMNS.values())[-1]}1').font.bold = True
        logger.debug("Trades sheet headers created")
