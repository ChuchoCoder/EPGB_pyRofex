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
                # Ensure headers exist in row 1
                self._ensure_headers_exist(homebroker_sheet)
                
                # Read existing symbols from column A (skip header row)
                symbols_range = homebroker_sheet.range('A2:A1000')  # Read up to 1000 rows
                symbols = symbols_range.value
                
                # Handle case where only one symbol exists (xlwings returns single value instead of list)
                if not isinstance(symbols, list):
                    symbols = [symbols] if symbols else []
                
                self._symbol_row_cache = {}
                for idx, cell_value in enumerate(symbols):
                    if cell_value and str(cell_value).strip():
                        # Row index is idx + 2 (skip header at row 1, and enumerate starts at 0)
                        self._symbol_row_cache[cell_value] = idx + 2
                
                logger.info(f"Built symbol row cache with {len(self._symbol_row_cache)} symbols from Excel")
                
                # Auto-populate missing symbols
                missing_symbols = [sym for sym in df.index if sym not in self._symbol_row_cache]
                if missing_symbols:
                    logger.info(f"Auto-populating {len(missing_symbols)} new symbols to HomeBroker sheet...")
                    self._add_symbols_to_sheet(homebroker_sheet, missing_symbols)
                    logger.info(f"✅ Added {len(missing_symbols)} new symbols to Excel")
            
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
            
            # Update cauciones table on the right side (columns R-U)
            self._update_cauciones_table(homebroker_sheet, df)
            
            self.update_stats['updates_performed'] += 1
            return True
            
        except Exception as e:
            logger.error(f"Error updating market data to HomeBroker sheet: {e}")
            self.update_stats['errors'] += 1
            return False
    
    def _ensure_headers_exist(self, sheet: xw.Sheet):
        """
        Ensure the HomeBroker sheet has proper headers in row 1.
        
        Args:
            sheet: xlwings Sheet object
        """
        try:
            # Check if headers already exist
            header_row = sheet.range('A1:O1').value
            
            # Define expected headers
            expected_headers = [
                'symbol', 'bid_size', 'bid', 'ask', 'ask_size', 'last', 'change',
                'open', 'high', 'low', 'previous_close', 'turnover', 'volume',
                'operations', 'datetime'
            ]
            
            # If headers don't match, write them
            if not header_row or header_row[0] != 'symbol':
                logger.info("Creating headers in HomeBroker sheet...")
                sheet.range('A1:O1').value = expected_headers
                # Optional: Format headers (bold)
                sheet.range('A1:O1').font.bold = True
                logger.debug("Headers created successfully")
                
        except Exception as e:
            logger.error(f"Error ensuring headers exist: {e}")
            raise
    
    def _add_symbols_to_sheet(self, sheet: xw.Sheet, symbols: list):
        """
        Add new symbols to the HomeBroker sheet.
        
        Args:
            sheet: xlwings Sheet object
            symbols: List of symbols to add
        """
        try:
            # Find the last row with data in column A (starting from row 2, since row 1 is header)
            last_row = 1  # Start with header row
            if hasattr(self, '_symbol_row_cache') and self._symbol_row_cache:
                last_row = max(self._symbol_row_cache.values())
            else:
                # Check for existing data starting from row 2
                existing_symbols = sheet.range('A2:A1000').value
                if isinstance(existing_symbols, list):
                    # Count non-empty cells
                    non_empty = [s for s in existing_symbols if s and str(s).strip()]
                    last_row = len(non_empty) + 1  # +1 for header
                elif existing_symbols:
                    last_row = 2  # One symbol at row 2
            
            # Add symbols starting from the next available row
            start_row = last_row + 1
            
            # Prepare bulk data for faster writing
            symbol_data = []
            for i, symbol in enumerate(symbols):
                row_num = start_row + i
                
                # Prepare row: [symbol, bid_size, bid, ask, ask_size, last, change, open, high, low, previous_close, turnover, volume, operations, datetime]
                row_data = [symbol] + [0] * 13 + ['']  # 13 numeric columns + 1 datetime column
                symbol_data.append(row_data)
                
                # Update cache
                self._symbol_row_cache[symbol] = row_num
            
            # Bulk write all symbols at once (much faster than individual writes)
            end_row = start_row + len(symbols) - 1
            sheet.range(f'A{start_row}:O{end_row}').value = symbol_data
            
            logger.debug(f"Added {len(symbols)} symbols to sheet starting at row {start_row}")
            
        except Exception as e:
            logger.error(f"Error adding symbols to sheet: {e}")
            raise
    
    def _update_cauciones_table(self, sheet: xw.Sheet, df: pd.DataFrame):
        """
        Update the cauciones table on the right side of the HomeBroker sheet.
        
        The table has Plazo (Period) in column R starting from row 2:
        - Row 2: "1 día" -> MERV - XMEV - PESOS - 1D (if exists)
        - Row 4: "3 días" -> MERV - XMEV - PESOS - 3D
        - Row 5: "4 días" -> MERV - XMEV - PESOS - 4D
        - etc.
        
        Columns to update:
        - S: Vencimiento (datetime)
        - T: Tasa (last price / rate)
        - U: Monto $ (volume * last)
        
        Args:
            sheet: xlwings Sheet object
            df: DataFrame with market data
        """
        try:
            # Build mapping from days to pyRofex symbols
            # Extract only caucion symbols from DataFrame
            caucion_symbols = [sym for sym in df.index if 'PESOS' in sym and 'D' in sym.split(' - ')[-1]]
            
            if not caucion_symbols:
                return  # No cauciones to update
            
            # Mapping from period (e.g., "3D") to row number in cauciones table
            period_to_row = {}
            for i in range(1, 61):  # Support 1-60 days
                period_to_row[f"{i}D"] = i + 1  # Row 2 is 1D, Row 3 is 2D, etc.
            period_to_row["60D"] = 34  # Special case: 60 días is at row 34
            
            # Collect updates for cauciones table
            updates = []
            
            for symbol in caucion_symbols:
                # Extract period from symbol (e.g., "MERV - XMEV - PESOS - 3D" -> "3D")
                parts = symbol.split(' - ')
                if len(parts) >= 4:
                    period = parts[3]  # e.g., "3D"
                    
                    # Get row number for this period
                    row_num = period_to_row.get(period)
                    if row_num is None:
                        continue
                    
                    # Get data for this symbol
                    if symbol in df.index:
                        row_data = df.loc[symbol]
                        
                        # Extract values
                        tasa = get_excel_safe_value(row_data.get('last', 0))
                        volume = get_excel_safe_value(row_data.get('volume', 0))
                        monto = tasa * volume if tasa and volume else 0
                        datetime_val = get_excel_safe_value(row_data.get('datetime', ''))
                        
                        # Store update: (row, [vencimiento, tasa, monto])
                        updates.append((row_num, [datetime_val, tasa, monto]))
            
            # Apply updates to Excel
            if updates:
                for row_num, values in updates:
                    # Update columns S (Vencimiento), T (Tasa), U (Monto $)
                    sheet.range(f'S{row_num}:U{row_num}').value = values
                
                logger.debug(f"Updated {len(updates)} cauciones in table (rows 2-34, columns S-U)")
            
        except Exception as e:
            logger.error(f"Error updating cauciones table: {e}")
            # Don't raise - this is a non-critical update
    
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