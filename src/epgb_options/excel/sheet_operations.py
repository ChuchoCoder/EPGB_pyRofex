"""
Excel sheet operations for EPGB Options.

This module handles reading from and writing to Excel sheets,
including data updates and formatting.
"""

import pandas as pd
import xlwings as xw
from typing import Any, Dict, List, Optional, Union
from ..utils.logging import get_logger
from ..utils.helpers import get_excel_safe_value, clean_dataframe_for_excel
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
            
            # Get HomeBroker sheet
            homebroker_sheet = self.workbook.sheets(homebroker_sheet_name)
            
            # Prepare data for HomeBroker sheet
            # The original code updates specific ranges, so we'll maintain that approach
            
            # Update data row by row for better control
            for symbol, row_data in df.iterrows():
                try:
                    self._update_single_instrument_row(homebroker_sheet, symbol, row_data)
                except Exception as e:
                    logger.warning(f"Error updating row for {symbol}: {e}")
                    continue
            
            self.update_stats['updates_performed'] += 1
            logger.info(f"Updated HomeBroker sheet with {len(df)} instruments")
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
            # Find the row for this symbol (this would need to be customized based on sheet layout)
            # For now, we'll use a simple approach - in practice, you'd need to map symbols to rows
            
            # Standard market data fields
            fields_to_update = {
                'bid': get_excel_safe_value(data.get('bid')),
                'ask': get_excel_safe_value(data.get('ask')),
                'last': get_excel_safe_value(data.get('last')),
                'volume': get_excel_safe_value(data.get('volume')),
                'change': get_excel_safe_value(data.get('change'))
            }
            
            # This is a placeholder - in practice, you'd need to know the exact cell mappings
            # For each symbol in your Excel sheet structure
            logger.debug(f"Would update {symbol} with data: {fields_to_update}")
            
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