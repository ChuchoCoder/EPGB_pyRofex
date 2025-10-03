"""
pyRofex API Client

This module handles the pyRofex API connection and configuration.
"""

import pyRofex

from ..config.pyrofex_config import (ACCOUNT, API_URL, ENVIRONMENT, PASSWORD,
                                     USER, WS_URL)
from ..utils.logging import get_logger

logger = get_logger(__name__)


class pyRofexClient:
    """pyRofex API client wrapper."""
    
    def __init__(self):
        """Initialize the pyRofex client."""
        self.is_initialized = False
        self.is_authenticated = False
        
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
        """Subscribe to real-time market data."""
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
            pyRofex.market_data_subscription(tickers=symbols, entries=entries)
            logger.info(f"Subscribed to market data for {len(symbols)} symbols")
            return True
        except Exception as e:
            logger.error(f"Failed to subscribe to market data: {e}")
            return False
    
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