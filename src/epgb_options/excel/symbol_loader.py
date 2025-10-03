"""
Symbol loader for EPGB Options.

This module loads financial instrument symbols from Excel sheets
and transforms them for pyRofex compatibility.
"""

from typing import Any, Dict, List, Optional

import pandas as pd
import xlwings as xw

from ..utils.helpers import transform_symbol_for_pyrofex
from ..utils.logging import get_logger
from ..utils.validation import validate_excel_range_data

logger = get_logger(__name__)


class SymbolLoader:
    """Loads financial instrument symbols from Excel sheets."""
    
    # Column mappings for different instrument types
    COLUMN_MAPPINGS = {
        'options': 'A2:A500',      # Options: Column A
        'acciones': 'C2:C500',     # Stocks: Column C  
        'bonos': 'E2:E500',        # Bonds: Column E
        'cedears': 'G2:G500',      # CEDEARs: Column G
        'letras': 'I2:I500',       # Letters: Column I
        'ons': 'K2:K500',          # ONs: Column K
        'panel_general': 'M2:M500' # Panel General: Column M
    }
    
    # Predefined cauciones (repos) list - only valid symbols from pyRofex API
    # Note: 1D, 2D, 7D, 8D, 9D are not available in the API
    CAUCIONES = [
        "MERV - XMEV - PESOS - 3D",
        "MERV - XMEV - PESOS - 4D",
        "MERV - XMEV - PESOS - 5D",
        "MERV - XMEV - PESOS - 6D",
        "MERV - XMEV - PESOS - 10D",
        "MERV - XMEV - PESOS - 11D",
        "MERV - XMEV - PESOS - 12D",
        "MERV - XMEV - PESOS - 13D",
        "MERV - XMEV - PESOS - 14D",
    ]
    
    def __init__(self, tickers_sheet: xw.Sheet):
        """
        Initialize symbol loader.
        
        Args:
            tickers_sheet: xlwings Sheet object for the Tickers sheet
        """
        self.tickers_sheet = tickers_sheet
        self.loaded_symbols = {}
    
    def get_options_list(self) -> pd.DataFrame:
        """
        Load options symbols from Excel.
        
        Returns:
            pd.DataFrame: DataFrame with options data
        """
        try:
            logger.debug("Loading options symbols from Excel")
            
            # Get data from Excel range
            rng = self.tickers_sheet.range(self.COLUMN_MAPPINGS['options']).expand()
            options_data = rng.value
            
            if not validate_excel_range_data(options_data):
                logger.warning("Invalid options data from Excel")
                return pd.DataFrame()
            
            # Process options data
            if isinstance(options_data, list):
                # Filter out None values and empty strings
                valid_options = [opt for opt in options_data if opt and str(opt).strip()]
            else:
                # Single value
                valid_options = [options_data] if options_data and str(options_data).strip() else []
            
            if not valid_options:
                logger.warning("No valid options found in Excel")
                return pd.DataFrame()
            
            # Transform symbols for pyRofex compatibility
            transformed_options = [transform_symbol_for_pyrofex(opt) for opt in valid_options]
            
            # Create DataFrame with necessary columns for options
            options_df = pd.DataFrame({
                'symbol': transformed_options,
                'bid': 0.0,
                'ask': 0.0,
                'bidsize': 0,
                'asksize': 0,
                'last': 0.0,
                'change': 0.0,
                'volume': 0,
                'datetime': pd.Timestamp.now()
            })
            
            options_df.set_index('symbol', inplace=True)
            
            self.loaded_symbols['options'] = options_df
            logger.info(f"Loaded {len(options_df)} options symbols")
            
            return options_df
            
        except Exception as e:
            logger.error(f"Error loading options list: {e}")
            return pd.DataFrame()
    
    def get_acciones_list(self) -> pd.DataFrame:
        """
        Load stock symbols from Excel.
        
        Returns:
            pd.DataFrame: DataFrame with stocks data
        """
        return self._load_securities_list('acciones', 'stocks')
    
    def get_bonos_list(self) -> pd.DataFrame:
        """
        Load bond symbols from Excel.
        
        Returns:
            pd.DataFrame: DataFrame with bonds data
        """
        return self._load_securities_list('bonos', 'bonds')
    
    def get_cedears_list(self) -> pd.DataFrame:
        """
        Load CEDEAR symbols from Excel.
        
        Returns:
            pd.DataFrame: DataFrame with CEDEARs data
        """
        return self._load_securities_list('cedears', 'CEDEARs')
    
    def get_letras_list(self) -> pd.DataFrame:
        """
        Load letters symbols from Excel.
        
        Returns:
            pd.DataFrame: DataFrame with letters data
        """
        return self._load_securities_list('letras', 'letters')
    
    def get_ons_list(self) -> pd.DataFrame:
        """
        Load ONs symbols from Excel.
        
        Returns:
            pd.DataFrame: DataFrame with ONs data
        """
        return self._load_securities_list('ons', 'ONs')
    
    def get_panel_general_list(self) -> pd.DataFrame:
        """
        Load Panel General symbols from Excel.
        
        Returns:
            pd.DataFrame: DataFrame with Panel General data
        """
        return self._load_securities_list('panel_general', 'Panel General')
    
    def get_cauciones_list(self) -> pd.DataFrame:
        """
        Get predefined cauciones (repos) list.
        
        Returns:
            pd.DataFrame: DataFrame with cauciones data
        """
        try:
            logger.debug("Creating cauciones list")
            
            # Create DataFrame with predefined cauciones
            cauciones_df = pd.DataFrame({
                'symbol': self.CAUCIONES,
                'bid': 0.0,
                'ask': 0.0,
                'bid_size': 0,
                'ask_size': 0,
                'last': 0.0,
                'change': 0.0,
                'volume': 0,
                'datetime': pd.Timestamp.now()
            })
            
            cauciones_df.set_index('symbol', inplace=True)
            
            self.loaded_symbols['cauciones'] = cauciones_df
            logger.info(f"Created {len(cauciones_df)} cauciones symbols")
            
            return cauciones_df
            
        except Exception as e:
            logger.error(f"Error creating cauciones list: {e}")
            return pd.DataFrame()
    
    def _load_securities_list(self, instrument_type: str, display_name: str) -> pd.DataFrame:
        """
        Generic method to load securities from Excel.
        
        Args:
            instrument_type: Key for column mapping
            display_name: Human-readable name for logging
            
        Returns:
            pd.DataFrame: DataFrame with securities data
        """
        try:
            logger.debug(f"Loading {display_name} symbols from Excel")
            
            if instrument_type not in self.COLUMN_MAPPINGS:
                logger.error(f"Unknown instrument type: {instrument_type}")
                return pd.DataFrame()
            
            # Get data from Excel range
            rng = self.tickers_sheet.range(self.COLUMN_MAPPINGS[instrument_type]).expand()
            securities_data = rng.value
            
            if not validate_excel_range_data(securities_data):
                logger.warning(f"Invalid {display_name} data from Excel")
                return pd.DataFrame()
            
            # Process securities data
            if isinstance(securities_data, list):
                # Filter out None values and empty strings
                valid_securities = [sec for sec in securities_data if sec and str(sec).strip()]
            else:
                # Single value
                valid_securities = [securities_data] if securities_data and str(securities_data).strip() else []
            
            if not valid_securities:
                logger.warning(f"No valid {display_name} found in Excel")
                return pd.DataFrame()
            
            # Transform symbols for pyRofex compatibility
            transformed_securities = [transform_symbol_for_pyrofex(sec) for sec in valid_securities]
            
            # Create DataFrame with necessary columns for securities
            securities_df = pd.DataFrame({
                'symbol': transformed_securities,
                'bid': 0.0,
                'ask': 0.0,
                'bid_size': 0,
                'ask_size': 0,
                'last': 0.0,
                'change': 0.0,
                'volume': 0,
                'datetime': pd.Timestamp.now()
            })
            
            securities_df.set_index('symbol', inplace=True)
            
            self.loaded_symbols[instrument_type] = securities_df
            logger.info(f"Loaded {len(securities_df)} {display_name} symbols")
            
            return securities_df
            
        except Exception as e:
            logger.error(f"Error loading {display_name} list: {e}")
            return pd.DataFrame()
    
    def get_all_symbols(self) -> Dict[str, pd.DataFrame]:
        """
        Load all symbol types from Excel.
        
        Returns:
            dict: Dictionary of DataFrames for each instrument type
        """
        try:
            logger.info("Loading all symbols from Excel")
            
            all_symbols = {
                'options': self.get_options_list(),
                'acciones': self.get_acciones_list(),
                'bonos': self.get_bonos_list(),
                'cedears': self.get_cedears_list(),
                'letras': self.get_letras_list(),
                'ons': self.get_ons_list(),
                'panel_general': self.get_panel_general_list(),
                'cauciones': self.get_cauciones_list()
            }
            
            # Log summary
            total_symbols = sum(len(df) for df in all_symbols.values())
            logger.info(f"Loaded total of {total_symbols} symbols across all instrument types")
            
            return all_symbols
            
        except Exception as e:
            logger.error(f"Error loading all symbols: {e}")
            return {}
    
    def get_combined_securities(self) -> pd.DataFrame:
        """
        Get combined DataFrame of all securities (excluding options).
        
        Returns:
            pd.DataFrame: Combined securities DataFrame
        """
        try:
            securities_dfs = [
                self.get_acciones_list(),
                self.get_bonos_list(), 
                self.get_cedears_list(),
                self.get_letras_list(),
                self.get_ons_list(),
                self.get_panel_general_list(),
                self.get_cauciones_list()
            ]
            
            # Filter out empty DataFrames
            valid_dfs = [df for df in securities_dfs if not df.empty]
            
            if valid_dfs:
                combined_df = pd.concat(valid_dfs, ignore_index=False)
                logger.info(f"Combined {len(combined_df)} securities symbols")
                return combined_df
            else:
                logger.warning("No valid securities data to combine")
                return pd.DataFrame()
                
        except Exception as e:
            logger.error(f"Error combining securities: {e}")
            return pd.DataFrame()
    
    def get_symbol_count_by_type(self) -> Dict[str, int]:
        """
        Get count of symbols by instrument type.
        
        Returns:
            dict: Symbol counts by type
        """
        counts = {}
        for instrument_type, df in self.loaded_symbols.items():
            counts[instrument_type] = len(df) if not df.empty else 0
        
        return counts