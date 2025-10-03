"""
Excel sheet operations for EPGB Options.

This module handles reading from and writing to Excel sheets,
including data updates and formatting.
"""

from typing import Any, Dict, List, Optional, Union

import pandas as pd
import xlwings as xw

from ..utils.helpers import clean_dataframe_for_excel, get_excel_safe_value
from ..utils.logging import get_logger
from ..utils.validation import validate_pandas_dataframe

logger = get_logger(__name__)


class SheetOperations:
    """Handles Excel sheet operations for reading and writing data."""
    
    def __init__(self, workbook: xw.Book):
        """
        Initialize sheet operations.
        
        Args:
            workbook: xlwings Workbook object
        """
        self.workbook = workbook
        self.update_stats = {
            'updates_performed': 0,
            'errors': 0,
            'last_update_time': None
        }
    
    def read_range(self, sheet_name: str, range_address: str) -> Any:
        """
        Read data from Excel range.
        
        Args:
            sheet_name: Name of the sheet
            range_address: Excel range address (e.g., 'A1:C10')
            
        Returns:
            Any: Data from the range
        """
        try:
            sheet = self.workbook.sheets(sheet_name)
            data = sheet.range(range_address).value
            logger.debug(f"Read data from {sheet_name}!{range_address}")
            return data
        except Exception as e:
            logger.error(f"Error reading range {sheet_name}!{range_address}: {e}")
            return None
    
    def write_range(self, sheet_name: str, range_address: str, data: Any) -> bool:
        """
        Write data to Excel range.
        
        Args:
            sheet_name: Name of the sheet
            range_address: Excel range address
            data: Data to write
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            sheet = self.workbook.sheets(sheet_name)
            sheet.range(range_address).value = data
            logger.debug(f"Wrote data to {sheet_name}!{range_address}")
            self.update_stats['updates_performed'] += 1
            return True
        except Exception as e:
            logger.error(f"Error writing to range {sheet_name}!{range_address}: {e}")
            self.update_stats['errors'] += 1
            return False
    
    def update_dataframe_to_sheet(self, sheet_name: str, df: pd.DataFrame, 
                                  start_cell: str = 'A1', include_index: bool = True,
                                  include_header: bool = True) -> bool:
        """
        Write DataFrame to Excel sheet.
        
        Args:
            sheet_name: Name of the sheet
            df: DataFrame to write
            start_cell: Starting cell for the data
            include_index: Whether to include DataFrame index
            include_header: Whether to include DataFrame header
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            if not validate_pandas_dataframe(df):
                logger.error("Invalid DataFrame for sheet update")
                return False
            
            if df.empty:
                logger.warning("Empty DataFrame - nothing to update")
                return True
            
            # Clean DataFrame for Excel compatibility
            clean_df = clean_dataframe_for_excel(df)
            
            # Get sheet
            sheet = self.workbook.sheets(sheet_name)
            
            # Write DataFrame to sheet
            sheet.range(start_cell).options(pd.DataFrame, 
                                           index=include_index, 
                                           header=include_header).value = clean_df
            
            logger.info(f"Updated {sheet_name} with {len(clean_df)} rows of data")
            self.update_stats['updates_performed'] += 1
            return True
            
        except Exception as e:
            logger.error(f"Error updating DataFrame to {sheet_name}: {e}")
            self.update_stats['errors'] += 1
            return False
    
    def update_market_data_to_homebroker_sheet(self, df: pd.DataFrame, 
                                               homebroker_sheet_name: str) -> bool:
        """
        Update market data to HomeBroker sheet with specific formatting.
        Uses bulk range update for maximum performance.
        
        Args:
            df: DataFrame with market data
            homebroker_sheet_name: Name of the HomeBroker sheet
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            if df.empty:
                logger.warning("No market data to update")
                return True
            
            logger.debug(f"Updating market data to {homebroker_sheet_name}")
            
            # DEBUG: Log DataFrame state for first few updates
            if self.update_stats['updates_performed'] < 2:
                sample_symbols = df.index[:3].tolist()
                logger.info(f"DataFrame sample (first 3 symbols): {sample_symbols}")
                for sym in sample_symbols:
                    logger.info(f"  {sym}: bid={df.loc[sym, 'bid']}, ask={df.loc[sym, 'ask']}, last={df.loc[sym, 'last']}")
            
            # Get HomeBroker sheet
            homebroker_sheet = self.workbook.sheets(homebroker_sheet_name)
            
            # Build symbol-to-row mapping ONCE (cache for performance)
            if not hasattr(self, '_symbol_row_cache') or self.update_stats['updates_performed'] == 0:
                symbols_range = homebroker_sheet.range('A:A')
                symbols = symbols_range.value
                self._symbol_row_cache = {}
                for idx, cell_value in enumerate(symbols):
                    if cell_value:
                        self._symbol_row_cache[cell_value] = idx + 1  # Excel rows are 1-indexed
                logger.info(f"Built symbol row cache with {len(self._symbol_row_cache)} symbols")
            
            # BULK UPDATE: Build 2D array for all data at once
            # Columns: B=bid_size, C=bid, D=ask, E=ask_size, F=last, G=change, H=open, I=high, J=low, K=previous_close, L=turnover, M=volume, N=operations, O=datetime
            field_order = ['bid_size', 'bid', 'ask', 'ask_size', 'last', 'change', 'open', 
                          'high', 'low', 'previous_close', 'turnover', 'volume', 'operations', 'datetime']
            
            # Collect updates by row number
            updates_by_row = {}
            for symbol, row_data in df.iterrows():
                row_index = self._symbol_row_cache.get(symbol)
                if row_index:
                    # Build row values
                    row_values = []
                    for field in field_order:
                        if field in row_data:
                            row_values.append(get_excel_safe_value(row_data[field]))
                        else:
                            row_values.append(0)
                    updates_by_row[row_index] = row_values
            
            # Find contiguous ranges for even faster bulk updates
            sorted_rows = sorted(updates_by_row.keys())
            if sorted_rows:
                min_row = sorted_rows[0]
                max_row = sorted_rows[-1]
                
                # Build 2D array with all rows (including gaps filled with existing data)
                bulk_data = []
                for row_idx in range(min_row, max_row + 1):
                    if row_idx in updates_by_row:
                        bulk_data.append(updates_by_row[row_idx])
                    else:
                        # Keep existing data for rows not in DataFrame (fill with None to skip update)
                        bulk_data.append([None] * len(field_order))
                
                # Single bulk write: Write entire range B{min}:O{max} at once
                range_address = f'B{min_row}:O{max_row}'
                homebroker_sheet.range(range_address).value = bulk_data
                
                logger.info(f"✅ Bulk updated {len(updates_by_row)} instruments in range {range_address}")
            
            self.update_stats['updates_performed'] += 1
            return True
            
        except Exception as e:
            logger.error(f"Error updating market data to HomeBroker sheet: {e}")
            self.update_stats['errors'] += 1
            return False
    
    def _update_single_instrument_row(self, sheet: xw.Sheet, symbol: str, data: pd.Series):
        """
        Update a single instrument row in the sheet.
        
        Args:
            sheet: xlwings Sheet object
            symbol: Instrument symbol
            data: Market data for the instrument
        """
        try:
            # Use cached row mapping instead of searching column A every time
            if hasattr(self, '_symbol_row_cache'):
                row_index = self._symbol_row_cache.get(symbol)
            else:
                # Fallback: search column A (slower)
                symbols_range = sheet.range('A:A')
                symbols = symbols_range.value
                row_index = None
                for idx, cell_value in enumerate(symbols):
                    if cell_value == symbol:
                        row_index = idx + 1
                        break
            
            if row_index is None:
                logger.warning(f"Symbol '{symbol}' not found in sheet column A")
                return
            
            # Define column mapping (adjust based on your Excel structure)
            # Assuming: A=symbol, B=bid_size, C=bid, D=ask, E=ask_size, F=last, G=change, etc.
            column_mapping = {
                'bid_size': 'B',
                'bid': 'C',
                'ask': 'D',
                'ask_size': 'E',
                'last': 'F',
                'change': 'G',
                'open': 'H',
                'high': 'I',
                'low': 'J',
                'previous_close': 'K',
                'turnover': 'L',
                'volume': 'M',
                'operations': 'N',
                'datetime': 'O'
            }
            
            # Batch update: Prepare all values in one list for faster Excel write
            # Build row data for columns B through O (14 columns)
            row_values = []
            for field in ['bid_size', 'bid', 'ask', 'ask_size', 'last', 'change', 'open', 
                         'high', 'low', 'previous_close', 'turnover', 'volume', 'operations', 'datetime']:
                if field in data:
                    row_values.append(get_excel_safe_value(data[field]))
                else:
                    row_values.append(0)
            
            # Single batch write for entire row (B:O)
            sheet.range(f'B{row_index}:O{row_index}').value = row_values
            
            logger.info(f"✅ Updated {symbol} at row {row_index} - bid={data.get('bid')}, ask={data.get('ask')}, last={data.get('last')}")
            
        except Exception as e:
            logger.warning(f"Error updating single row for {symbol}: {e}")
    
    def clear_range(self, sheet_name: str, range_address: str) -> bool:
        """
        Clear data from Excel range.
        
        Args:
            sheet_name: Name of the sheet
            range_address: Excel range address to clear
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            sheet = self.workbook.sheets(sheet_name)
            sheet.range(range_address).clear_contents()
            logger.debug(f"Cleared range {sheet_name}!{range_address}")
            return True
        except Exception as e:
            logger.error(f"Error clearing range {sheet_name}!{range_address}: {e}")
            return False
    
    def get_sheet_info(self, sheet_name: str) -> Dict[str, Any]:
        """
        Get information about a sheet.
        
        Args:
            sheet_name: Name of the sheet
            
        Returns:
            dict: Sheet information
        """
        try:
            sheet = self.workbook.sheets(sheet_name)
            return {
                'name': sheet.name,
                'used_range': str(sheet.used_range.address) if sheet.used_range else None,
                'visible': sheet.visible,
                'exists': True
            }
        except Exception as e:
            logger.error(f"Error getting sheet info for {sheet_name}: {e}")
            return {'exists': False, 'error': str(e)}
    
    def format_range(self, sheet_name: str, range_address: str, 
                     format_dict: Dict[str, Any]) -> bool:
        """
        Apply formatting to Excel range.
        
        Args:
            sheet_name: Name of the sheet
            range_address: Excel range address
            format_dict: Dictionary with formatting options
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            sheet = self.workbook.sheets(sheet_name)
            range_obj = sheet.range(range_address)
            
            # Apply formatting based on format_dict
            for format_key, format_value in format_dict.items():
                if format_key == 'number_format':
                    range_obj.number_format = format_value
                elif format_key == 'font_bold':
                    range_obj.font.bold = format_value
                elif format_key == 'font_size':
                    range_obj.font.size = format_value
                elif format_key == 'background_color':
                    range_obj.color = format_value
                # Add more formatting options as needed
            
            logger.debug(f"Applied formatting to {sheet_name}!{range_address}")
            return True
            
        except Exception as e:
            logger.error(f"Error formatting range {sheet_name}!{range_address}: {e}")
            return False
    
    def copy_range(self, source_sheet: str, source_range: str,
                   dest_sheet: str, dest_range: str) -> bool:
        """
        Copy data from one range to another.
        
        Args:
            source_sheet: Source sheet name
            source_range: Source range address
            dest_sheet: Destination sheet name
            dest_range: Destination range address
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Get source data
            source_data = self.read_range(source_sheet, source_range)
            if source_data is None:
                return False
            
            # Write to destination
            return self.write_range(dest_sheet, dest_range, source_data)
            
        except Exception as e:
            logger.error(f"Error copying range: {e}")
            return False
    
    def get_update_stats(self) -> Dict[str, Any]:
        """
        Get update statistics.
        
        Returns:
            dict: Update statistics
        """
        return self.update_stats.copy()
    
    def reset_stats(self):
        """Reset update statistics."""
        self.update_stats = {
            'updates_performed': 0,
            'errors': 0,
            'last_update_time': None
        }