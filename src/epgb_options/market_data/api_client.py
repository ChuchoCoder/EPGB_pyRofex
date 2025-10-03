"""
pyRofex API Client

This module handles the pyRofex API connection and configuration.
"""

from typing import List, Set, Tuple

import pyRofex

from ..config.pyrofex_config import (ACCOUNT, API_URL, ENVIRONMENT, PASSWORD,
                                     USER, WS_URL)
from ..utils.logging import get_logger
from .instrument_cache import InstrumentCache

logger = get_logger(__name__)


class pyRofexClient:
    """pyRofex API client wrapper."""
    
    def __init__(self):
        """Initialize the pyRofex client."""
        self.is_initialized = False
        self.is_authenticated = False
        self.instrument_cache = InstrumentCache(ttl_minutes=30)
        self._valid_instruments: Set[str] = set()
        
    def initialize(self):
        """Initialize the pyRofex connection."""
        try:
            # Set environment parameters
            pyRofex._set_environment_parameter('url', API_URL, getattr(pyRofex.Environment, ENVIRONMENT))
            pyRofex._set_environment_parameter('ws', WS_URL, getattr(pyRofex.Environment, ENVIRONMENT))
            
            # Initialize
            pyRofex.initialize(environment=getattr(pyRofex.Environment, ENVIRONMENT),
                             user=USER, 
                             password=PASSWORD,
                             account=ACCOUNT)
            
            self.is_initialized = True
            logger.info(f"pyRofex initialized with environment: {ENVIRONMENT}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize pyRofex: {e}")
            return False
    
    def fetch_available_instruments(self, force_refresh: bool = False) -> Set[str]:
        """
        Fetch available instruments from pyRofex API.
        Uses cache if available and not expired.
        
        Args:
            force_refresh: Force refresh from API even if cache is valid
            
        Returns:
            Set of valid instrument symbols
        """
        try:
            # Try cache first unless force refresh
            if not force_refresh:
                cached_symbols = self.instrument_cache.get_instrument_symbols()
                if cached_symbols:
                    self._valid_instruments = cached_symbols
                    logger.info(f"Loaded {len(cached_symbols)} instruments from cache")
                    return cached_symbols
            
            # Fetch from API
            logger.info("Fetching available instruments from pyRofex API...")
            instrumentsResponse = pyRofex.get_all_instruments()
            
            if not instrumentsResponse:
                logger.warning("No instruments returned from API")
                return set()
            
            instruments = instrumentsResponse['instruments']
            
            if not instruments:
                logger.warning("No instruments found in API response")
                return set()

            # Log response structure for debugging
            logger.debug(f"API returned {len(instruments)} instruments, type: {type(instruments)}")
            if instruments and len(instruments) > 0:
                logger.debug(f"First instrument type: {type(instruments[0])}, sample: {instruments[0] if isinstance(instruments[0], str) else str(instruments[0])[:100]}")
            
            # Save to cache
            self.instrument_cache.save_instruments(
                instruments,
                metadata={
                    'environment': ENVIRONMENT,
                    'fetched_by': 'pyRofexClient'
                }
            )
            
            # Extract symbols - handle both dict and string formats
            symbols = set()
            for instrument in instruments:
                if isinstance(instrument, str):
                    # Already a symbol string
                    symbols.add(instrument)
                elif isinstance(instrument, dict):
                    # Extract symbol from dict
                    symbol = instrument.get('symbol') or instrument.get('instrumentId', {}).get('symbol')
                    if symbol:
                        symbols.add(symbol)
                else:
                    logger.warning(f"Unexpected instrument type: {type(instrument)}")
            
            self._valid_instruments = symbols
            logger.info(f"Fetched {len(symbols)} instruments from API")
            return symbols
            
        except Exception as e:
            logger.error(f"Error fetching instruments: {e}")
            # Return cached symbols as fallback
            cached_symbols = self.instrument_cache.get_instrument_symbols()
            if cached_symbols:
                logger.warning(f"Using cached instruments as fallback ({len(cached_symbols)} symbols)")
                self._valid_instruments = cached_symbols
                return cached_symbols
            return set()
    
    def validate_symbols(self, symbols: List[str]) -> Tuple[List[str], List[str]]:
        """
        Validate symbols against available instruments.
        
        Args:
            symbols: List of symbols to validate
            
        Returns:
            Tuple of (valid_symbols, invalid_symbols)
        """
        if not self._valid_instruments:
            logger.warning("No instruments loaded, fetching now...")
            self.fetch_available_instruments()
        
        if not self._valid_instruments:
            logger.error("Cannot validate symbols - no instruments available")
            return symbols, []  # Allow all symbols if we can't validate
        
        valid = []
        invalid = []
        
        for symbol in symbols:
            if symbol in self._valid_instruments:
                valid.append(symbol)
            else:
                invalid.append(symbol)
        
        if invalid:
            logger.warning(f"Found {len(invalid)} invalid symbols: {invalid[:5]}{'...' if len(invalid) > 5 else ''}")
        
        logger.info(f"Symbol validation: {len(valid)} valid, {len(invalid)} invalid out of {len(symbols)} total")
        return valid, invalid
    
    def get_market_data(self, symbols, entries=None):
        """Get market data for symbols."""
        if not self.is_initialized:
            raise RuntimeError("Client not initialized. Call initialize() first.")
            
        if entries is None:
            entries = [
                pyRofex.MarketDataEntry.BIDS,
                pyRofex.MarketDataEntry.OFFERS, 
                pyRofex.MarketDataEntry.LAST,
                pyRofex.MarketDataEntry.TRADE_VOLUME
            ]
            
        try:
            return pyRofex.get_market_data(symbols, entries)
        except Exception as e:
            logger.error(f"Failed to get market data: {e}")
            raise
    
    def subscribe_market_data(self, symbols, entries=None):
        """
        Subscribe to real-time market data.
        Validates symbols before subscribing.
        
        Args:
            symbols: List of symbols to subscribe to
            entries: Market data entries to subscribe to
            
        Returns:
            Tuple of (success: bool, valid_symbols: List[str], invalid_symbols: List[str])
        """
        if not self.is_initialized:
            raise RuntimeError("Client not initialized. Call initialize() first.")
        
        # Validate symbols first
        valid_symbols, invalid_symbols = self.validate_symbols(symbols)
        
        if not valid_symbols:
            logger.error("No valid symbols to subscribe to")
            return False, [], invalid_symbols
        
        if invalid_symbols:
            logger.warning(f"Skipping {len(invalid_symbols)} invalid symbols: {invalid_symbols}")
            
        if entries is None:
            entries = [
                pyRofex.MarketDataEntry.BIDS,
                pyRofex.MarketDataEntry.OFFERS,
                pyRofex.MarketDataEntry.LAST,
                pyRofex.MarketDataEntry.TRADE_VOLUME
            ]
            
        try:
            pyRofex.market_data_subscription(tickers=valid_symbols, entries=entries)
            logger.info(f"Subscribed to market data for {len(valid_symbols)} valid symbols")
            return True, valid_symbols, invalid_symbols
        except Exception as e:
            logger.error(f"Failed to subscribe to market data: {e}")
            return False, valid_symbols, invalid_symbols
    
    def set_market_data_handler(self, handler):
        """Register (add) the market data message handler (pyRofex 0.5.x API)."""
        if not callable(handler):
            raise ValueError("Handler must be callable")
        # pyRofex 0.5.0 provides add_websocket_market_data_handler
        if hasattr(pyRofex, 'add_websocket_market_data_handler'):
            pyRofex.add_websocket_market_data_handler(handler)
            logger.info("Market data handler registered")
        else:
            raise AttributeError("pyRofex module missing add_websocket_market_data_handler")
    
    def set_error_handler(self, handler):
        """Register (add) the websocket error handler.""" 
        if not callable(handler):
            raise ValueError("Handler must be callable")
        if hasattr(pyRofex, 'add_websocket_error_handler'):
            pyRofex.add_websocket_error_handler(handler)
            logger.info("Error handler registered")
        else:
            logger.warning("pyRofex missing add_websocket_error_handler; handler not set")
    
    def set_exception_handler(self, handler):
        """Set the websocket exception handler (name differs in 0.5.x)."""
        if not callable(handler):
            raise ValueError("Handler must be callable")
        if hasattr(pyRofex, 'set_websocket_exception_handler'):
            pyRofex.set_websocket_exception_handler(handler)
            logger.info("Exception handler set")
        else:
            logger.warning("pyRofex missing set_websocket_exception_handler; exception handler not set")
    
    def close_connection(self):
        """Close the pyRofex connection."""
        if self.is_initialized:
            try:
                pyRofex.close_websocket_connection()
                logger.info("pyRofex connection closed")
            except Exception as e:
                logger.warning(f"Error closing connection: {e}")
        
        self.is_initialized = False
        self.is_authenticated = False