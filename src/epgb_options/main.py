"""
Main application entry point for EPGB Options.

This module provides the main application logic and coordinates
all the different components.
"""

import time
from datetime import datetime
from typing import Any, Dict

import pandas as pd

from .config import (EXCEL_FILE, EXCEL_PATH, SHEET_HOMEBROKER, SHEET_TICKERS,
                     validate_excel_config, validate_pyRofex_config)
from .excel import SheetOperations, SymbolLoader, WorkbookManager
from .market_data import DataProcessor, WebSocketHandler, pyRofexClient
from .utils import get_logger, log_connection_event, setup_logging

logger = get_logger(__name__)


class EPGBOptionsApp:
    """Main EPGB Options application class."""
    
    def __init__(self):
        """Initialize the application."""
        self.api_client = None
        self.websocket_handler = None
        self.data_processor = None
        self.workbook_manager = None
        self.symbol_loader = None
        self.sheet_operations = None
        
        # Data storage
        self.options_df = pd.DataFrame()
        self.everything_df = pd.DataFrame()
        
        # Application state
        self.is_running = False
        self.last_update_time = None
    
    def initialize(self) -> bool:
        """
        Initialize all application components.
        
        Returns:
            bool: True if initialization successful, False otherwise
        """
        try:
            logger.info("Initializing EPGB Options application")
            
            # Setup logging
            setup_logging()
            
            # Validate configurations
            if not self._validate_configurations():
                return False
            
            # Initialize Excel components
            if not self._initialize_excel_components():
                return False
            
            # Load symbols from Excel
            if not self._load_symbols():
                return False
            
            # Initialize market data components
            if not self._initialize_market_data_components():
                return False
            
            logger.info("✅ Application initialization completed successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize application: {e}")
            return False
    
    def _validate_configurations(self) -> bool:
        """Validate all configuration files."""
        logger.info("Validating configurations...")
        
        # Validate Excel configuration
        excel_errors = validate_excel_config()
        if excel_errors:
            logger.error("Excel configuration errors:")
            for error in excel_errors:
                logger.error(f"  - {error}")
            return False
        
        # Validate pyRofex configuration
        pyrofex_errors = validate_pyRofex_config()
        if pyrofex_errors:
            logger.error("pyRofex configuration errors:")
            for error in pyrofex_errors:
                logger.error(f"  - {error}")
            
            # Check for placeholder values specifically
            if any("placeholder" in error.lower() for error in pyrofex_errors):
                logger.error("🛑 STOPPING EXECUTION - Manual credential configuration required")
                logger.error("Please configure your credentials in:")
                logger.error("   - pyRofex_config.py (or)")
                logger.error("   - Environment variables: PYROFEX_USER, PYROFEX_PASSWORD, PYROFEX_ACCOUNT")
                return False
        
        logger.info("✅ Configuration validation passed")
        return True
    
    def _initialize_excel_components(self) -> bool:
        """Initialize Excel-related components."""
        try:
            logger.info("Initializing Excel components...")
            
            # Initialize workbook manager
            self.workbook_manager = WorkbookManager(EXCEL_FILE, EXCEL_PATH)
            if not self.workbook_manager.connect():
                return False
            
            # Get tickers sheet
            tickers_sheet = self.workbook_manager.get_sheet(SHEET_TICKERS)
            if not tickers_sheet:
                logger.error(f"Could not access {SHEET_TICKERS} sheet")
                return False
            
            # Initialize symbol loader
            self.symbol_loader = SymbolLoader(tickers_sheet)
            
            # Initialize sheet operations
            self.sheet_operations = SheetOperations(self.workbook_manager.workbook)
            
            logger.info("✅ Excel components initialized")
            return True
            
        except Exception as e:
            logger.error(f"Error initializing Excel components: {e}")
            return False
    
    def _load_symbols(self) -> bool:
        """Load symbols from Excel sheets."""
        try:
            logger.info("Loading symbols from Excel...")
            
            # Load all symbol types
            all_symbols = self.symbol_loader.get_all_symbols()
            
            # Store options separately
            self.options_df = all_symbols.get('options', pd.DataFrame())
            
            # Combine other securities
            securities_to_combine = ['acciones', 'bonos', 'cedears', 'letras', 'ons', 'panel_general', 'cauciones']
            securities_dfs = [all_symbols.get(key, pd.DataFrame()) for key in securities_to_combine]
            valid_securities = [df for df in securities_dfs if not df.empty]
            
            if valid_securities:
                self.everything_df = pd.concat(valid_securities, ignore_index=False)
            else:
                self.everything_df = pd.DataFrame()
            
            # Log summary
            symbol_counts = self.symbol_loader.get_symbol_count_by_type()
            logger.info("Symbol loading summary:")
            for symbol_type, count in symbol_counts.items():
                logger.info(f"  - {symbol_type}: {count} symbols")
            
            total_symbols = len(self.options_df) + len(self.everything_df)
            logger.info(f"✅ Total symbols loaded: {total_symbols}")
            
            return total_symbols > 0
            
        except Exception as e:
            logger.error(f"Error loading symbols: {e}")
            return False
    
    def _initialize_market_data_components(self) -> bool:
        """Initialize market data components."""
        try:
            logger.info("Initializing market data components...")
            
            # Initialize API client
            self.api_client = pyRofexClient()
            if not self.api_client.initialize():
                logger.error("Failed to initialize pyRofex API client")
                return False
            
            # Initialize WebSocket handler
            self.websocket_handler = WebSocketHandler()
            self.websocket_handler.set_data_references(self.options_df, self.everything_df)
            self.websocket_handler.set_update_callback(self._on_data_update)
            
            # Initialize data processor
            self.data_processor = DataProcessor()
            
            # Set up WebSocket handlers
            self.api_client.set_market_data_handler(self.websocket_handler.market_data_handler)
            self.api_client.set_error_handler(self.websocket_handler.websocket_error_handler)
            self.api_client.set_exception_handler(self.websocket_handler.websocket_exception_handler)
            
            logger.info("✅ Market data components initialized")
            return True
            
        except Exception as e:
            logger.error(f"Error initializing market data components: {e}")
            return False
    
    def _on_data_update(self, symbol: str, message: Dict[str, Any]):
        """
        Callback for when market data is updated.
        
        Args:
            symbol: Updated symbol
            message: Market data message
        """
        self.last_update_time = datetime.now()
        logger.debug(f"Data update callback for {symbol}")
        
        # You could trigger Excel updates here or batch them
        # For now, we'll just log the update
    
    def start_market_data_subscription(self) -> bool:
        """Start subscribing to market data."""
        try:
            logger.info("Starting market data subscription...")
            
            # Fetch available instruments first
            logger.info("Fetching available instruments from pyRofex...")
            available_instruments = self.api_client.fetch_available_instruments()
            logger.info(f"Found {len(available_instruments)} available instruments")
            
            # Subscribe to options
            if not self.options_df.empty:
                options_symbols = list(self.options_df.index)
                success, valid_symbols, invalid_symbols = self.api_client.subscribe_market_data(options_symbols)
                
                if invalid_symbols:
                    logger.warning(f"Skipped {len(invalid_symbols)} invalid option symbols")
                    
                if not success or not valid_symbols:
                    logger.error("Failed to subscribe to options data")
                    return False
                    
                logger.info(f"Subscribed to {len(valid_symbols)} options")
            
            # Subscribe to other securities  
            if not self.everything_df.empty:
                securities_symbols = list(self.everything_df.index)
                success, valid_symbols, invalid_symbols = self.api_client.subscribe_market_data(securities_symbols)
                
                if invalid_symbols:
                    logger.warning(f"Skipped {len(invalid_symbols)} invalid security symbols")
                    
                if not success or not valid_symbols:
                    logger.error("Failed to subscribe to securities data")
                    return False
                    
                logger.info(f"Subscribed to {len(valid_symbols)} securities")
            
            log_connection_event("Market Data Subscription", "Started successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error starting market data subscription: {e}")
            return False
    
    def update_excel_with_current_data(self) -> bool:
        """Update Excel with current market data."""
        try:
            logger.debug("Updating Excel with current data...")
            
            # Update HomeBroker sheet with securities data
            if not self.everything_df.empty:
                success = self.sheet_operations.update_market_data_to_homebroker_sheet(
                    self.everything_df, SHEET_HOMEBROKER
                )
                if not success:
                    logger.warning("Failed to update HomeBroker sheet")
            
            # You could add options sheet updates here if needed
            
            logger.debug("Excel update completed")
            return True
            
        except Exception as e:
            logger.error(f"Error updating Excel: {e}")
            return False
    
    def run(self):
        """Run the main application loop."""
        try:
            logger.info("🚀 Starting EPGB Options Market Data application")
            
            if not self.initialize():
                logger.error("Initialization failed - stopping application")
                return
            
            if not self.start_market_data_subscription():
                logger.error("Market data subscription failed - stopping application")
                return
            
            self.is_running = True
            logger.info("✅ Application running - market data streaming started")
            
            # Wait for initial market data to populate (give WebSocket time to receive first batch)
            logger.info("Waiting for initial market data to populate...")
            time.sleep(2)
            logger.info("Starting Excel updates")
            
            # Main application loop
            try:
                while self.is_running:
                    # Update Excel periodically
                    self.update_excel_with_current_data()
                    
                    # Sleep for a short interval
                    time.sleep(1)
                    
            except KeyboardInterrupt:
                logger.info("Keyboard interrupt received - shutting down gracefully")
            
        except Exception as e:
            logger.error(f"Error in main application loop: {e}")
        finally:
            self.shutdown()
    
    def shutdown(self):
        """Shutdown the application gracefully."""
        try:
            logger.info("Shutting down application...")
            
            self.is_running = False
            
            # Close API client
            if self.api_client:
                self.api_client.close_connection()
            
            # Disconnect from Excel
            if self.workbook_manager:
                self.workbook_manager.disconnect()
            
            logger.info("✅ Application shutdown completed")
            
        except Exception as e:
            logger.error(f"Error during shutdown: {e}")
    
    def get_status_report(self) -> Dict[str, Any]:
        """
        Get application status report.
        
        Returns:
            dict: Status information
        """
        try:
            return {
                'is_running': self.is_running,
                'last_update_time': self.last_update_time,
                'options_count': len(self.options_df),
                'securities_count': len(self.everything_df),
                'websocket_stats': self.websocket_handler.get_connection_stats() if self.websocket_handler else {},
                'processing_stats': self.data_processor.get_processing_stats() if self.data_processor else {},
                'excel_connected': self.workbook_manager.is_connected() if self.workbook_manager else False
            }
        except Exception as e:
            logger.error(f"Error getting status report: {e}")
            return {'error': str(e)}


def main():
    """Main entry point for the application."""
    app = EPGBOptionsApp()
    app.run()


if __name__ == "__main__":
    main()