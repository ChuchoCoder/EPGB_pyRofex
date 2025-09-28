"""
Excel workbook manager for EPGB Options.

This module handles Excel workbook connections and management.
"""

import xlwings as xw
from pathlib import Path
from typing import Optional
from ..utils.logging import get_logger

logger = get_logger(__name__)


class WorkbookManager:
    """Manages Excel workbook connections and operations."""
    
    def __init__(self, excel_file: str, excel_path: str = "./"):
        """
        Initialize workbook manager.
        
        Args:
            excel_file: Excel file name
            excel_path: Path to Excel file
        """
        self.excel_file = excel_file
        self.excel_path = excel_path
        self.workbook = None
        self._is_connected = False
    
    def connect(self) -> bool:
        """
        Connect to Excel workbook.
        
        Returns:
            bool: True if connection successful, False otherwise
        """
        try:
            # Construct full path
            full_path = Path(self.excel_path) / self.excel_file
            
            # Check if file exists
            if not full_path.exists():
                logger.error(f"Excel file not found: {full_path}")
                return False
            
            # Connect to workbook
            self.workbook = xw.Book(str(full_path))
            self._is_connected = True
            
            logger.info(f"Connected to Excel workbook: {self.excel_file}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect to Excel workbook: {e}")
            self._is_connected = False
            return False
    
    def disconnect(self):
        """Disconnect from Excel workbook."""
        if self.workbook and self._is_connected:
            try:
                # Note: We don't close the workbook as it might be in use
                # Just clear our reference
                self.workbook = None
                self._is_connected = False
                logger.info("Disconnected from Excel workbook")
            except Exception as e:
                logger.warning(f"Error during disconnect: {e}")
    
    def get_sheet(self, sheet_name: str) -> Optional[xw.Sheet]:
        """
        Get a specific sheet from the workbook.
        
        Args:
            sheet_name: Name of the sheet to retrieve
            
        Returns:
            xlwings.Sheet or None: Sheet object if found, None otherwise
        """
        if not self.is_connected():
            logger.error("Not connected to workbook")
            return None
        
        try:
            sheet = self.workbook.sheets(sheet_name)
            logger.debug(f"Retrieved sheet: {sheet_name}")
            return sheet
        except Exception as e:
            logger.error(f"Failed to get sheet '{sheet_name}': {e}")
            return None
    
    def is_connected(self) -> bool:
        """
        Check if connected to workbook.
        
        Returns:
            bool: True if connected, False otherwise
        """
        return self._is_connected and self.workbook is not None
    
    def get_workbook_info(self) -> dict:
        """
        Get information about the connected workbook.
        
        Returns:
            dict: Workbook information
        """
        if not self.is_connected():
            return {"connected": False}
        
        try:
            return {
                "connected": True,
                "file_name": self.excel_file,
                "file_path": self.excel_path,
                "sheet_names": [sheet.name for sheet in self.workbook.sheets]
            }
        except Exception as e:
            logger.error(f"Error getting workbook info: {e}")
            return {"connected": True, "error": str(e)}
    
    def save_workbook(self) -> bool:
        """
        Save the workbook.
        
        Returns:
            bool: True if saved successfully, False otherwise
        """
        if not self.is_connected():
            logger.error("Cannot save - not connected to workbook")
            return False
        
        try:
            self.workbook.save()
            logger.info("Workbook saved successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to save workbook: {e}")
            return False
    
    def __enter__(self):
        """Context manager entry."""
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.disconnect()