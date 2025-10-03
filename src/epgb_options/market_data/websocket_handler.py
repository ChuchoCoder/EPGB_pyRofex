"""
WebSocket handler for EPGB Options.

This module handles WebSocket connections, message processing, and error handling
for real-time market data from pyRofex.
"""

from datetime import datetime
from typing import Any, Callable, Dict, Optional

import pandas as pd

from ..utils.helpers import get_excel_safe_value
from ..utils.logging import (get_logger, log_connection_event,
                             log_market_data_event)
from ..utils.validation import (safe_float_conversion, safe_int_conversion,
                                validate_market_data)

logger = get_logger(__name__)


class WebSocketHandler:
    """Handles WebSocket connections and message processing."""
    
    def __init__(self):
        """Initialize WebSocket handler."""
        self.is_connected = False
        self.connection_stats = {
            'messages_received': 0,
            'messages_processed': 0, 
            'errors': 0,
            'last_message_time': None,
            'connection_start': None
        }
        
        # Data storage references (will be set by main application)
        self.options_df = None
        self.everything_df = None
        
        # Callbacks
        self.on_data_update = None  # Callback for when data is updated
    
    def set_data_references(self, options_df: pd.DataFrame, everything_df: pd.DataFrame):
        """Set references to main DataFrames."""
        self.options_df = options_df
        self.everything_df = everything_df
    
    def set_update_callback(self, callback: Callable):
        """Set callback function for data updates."""
        self.on_data_update = callback
    
    def market_data_handler(self, message: Dict[str, Any]):
        """
        Handle market data messages from pyRofex WebSocket.
        
        Expected pyRofex message structure:
        {
            "symbol": "MERV - XMEV - YPFD - 24hs",
            "bid": 150.50,
            "ask": 151.00,
            "bid_size": 1000,
            "ask_size": 500,
            "last": 150.75,
            "change": 0.025,
            "open": 150.25,
            "high": 151.50,
            "low": 149.80,
            "previous_close": 150.00,
            "turnover": 1500000.0,
            "volume": 10000,
            "operations": 45,
            "datetime": "2025-09-27T15:30:45.123Z"
        }
        
        Args:
            message: Market data message from pyRofex
        """
        self.connection_stats['messages_received'] += 1
        self.connection_stats['last_message_time'] = datetime.now()
        
        # DEBUG: Log raw message structure for first few messages
        if self.connection_stats['messages_received'] <= 3:
            logger.info(f"RAW MESSAGE #{self.connection_stats['messages_received']}: {message}")
        
        try:
            # Validate message structure
            if not validate_market_data(message):
                logger.warning(f"Invalid market data message: {message}")
                self.connection_stats['errors'] += 1
                return
            
            # Extract symbol
            symbol = message.get('instrumentId', {}).get('symbol')
            if not symbol:
                logger.warning("No symbol in market data message")
                return
            
            # Process market data
            self._process_market_data(symbol, message)
            self.connection_stats['messages_processed'] += 1
            
            log_market_data_event(symbol, "data_update")
            
            # Notify callback if set
            if self.on_data_update:
                try:
                    self.on_data_update(symbol, message)
                except Exception as e:
                    logger.error(f"Error in update callback: {e}")
        
        except Exception as e:
            self._handle_processing_error(e, message)
    
    def _process_market_data(self, symbol: str, message: Dict[str, Any]):
        """Process market data and update appropriate DataFrame."""
        
        # Extract market data fields
        market_data = message.get('marketData', {})
        
        # DEBUG: Log market data extraction for first symbol
        if self.connection_stats['messages_processed'] < 2:
            logger.info(f"Processing symbol: {symbol}")
            logger.info(f"Market data fields: {market_data}")
        
        # Extract nested fields (pyRofex 0.5.0 uses nested structures)
        # BIDS and OFFERS are arrays of price levels
        bids = market_data.get('BI', [])
        offers = market_data.get('OF', [])
        last_trade = market_data.get('LA', {})
        
        # Extract best bid/offer (first level in the book)
        best_bid = bids[0] if bids and isinstance(bids, list) else {}
        best_offer = offers[0] if offers and isinstance(offers, list) else {}
        
        # Create data row compatible with existing Excel structure
        data_row = {
            'bid_size': safe_int_conversion(best_bid.get('size') if isinstance(best_bid, dict) else None),
            'bid': safe_float_conversion(best_bid.get('price') if isinstance(best_bid, dict) else None),
            'ask': safe_float_conversion(best_offer.get('price') if isinstance(best_offer, dict) else None),
            'ask_size': safe_int_conversion(best_offer.get('size') if isinstance(best_offer, dict) else None),
            'last': safe_float_conversion(last_trade.get('price') if isinstance(last_trade, dict) else None),
            'change': safe_float_conversion(market_data.get('CH')) / 100 if market_data.get('CH') else 0.0,
            'open': safe_float_conversion(market_data.get('OP')),
            'high': safe_float_conversion(market_data.get('HI')),
            'low': safe_float_conversion(market_data.get('LO')),
            'previous_close': safe_float_conversion(market_data.get('CL')),
            'turnover': safe_float_conversion(market_data.get('TV')),
            'volume': safe_int_conversion(last_trade.get('size') if isinstance(last_trade, dict) else market_data.get('EV')),
            'operations': safe_int_conversion(market_data.get('NV')),
            'datetime': pd.Timestamp.now()
        }
        
        # DEBUG: Log extracted values
        if self.connection_stats['messages_processed'] < 2:
            logger.info(f"Extracted data row: {data_row}")
        
        # Create DataFrame for this update
        update_df = pd.DataFrame([data_row], index=[symbol])
        
        # Determine which DataFrame to update based on symbol characteristics
        if self._is_options_symbol(symbol):
            self._update_options_data(symbol, update_df)
        else:
            self._update_securities_data(symbol, update_df)
        
        logger.debug(f"Updated {symbol}: last={data_row['last']}, bid={data_row['bid']}, ask={data_row['ask']}")
    
    def _is_options_symbol(self, symbol: str) -> bool:
        """Determine if symbol represents an options contract."""
        options_indicators = ['CALL', 'PUT', 'C ', 'P ', 'OPTION']
        return any(indicator in symbol.upper() for indicator in options_indicators)
    
    def _update_options_data(self, symbol: str, update_df: pd.DataFrame):
        """Update options DataFrame."""
        if self.options_df is not None and not self.options_df.empty:
            # Rename columns for options compatibility
            update_df = update_df.rename(columns={"bid_size": "bidsize", "ask_size": "asksize"})
            update_df = update_df.drop(['expiration', 'strike', 'kind'], axis=1, errors='ignore')
            
            # Use .loc[] assignment instead of .update() to ensure values are set
            if symbol in self.options_df.index:
                for col in update_df.columns:
                    if col in self.options_df.columns:
                        self.options_df.loc[symbol, col] = update_df.loc[symbol, col]
        else:
            logger.warning(f"Options DataFrame not initialized for symbol: {symbol}")
    
    def _update_securities_data(self, symbol: str, update_df: pd.DataFrame):
        """Update securities DataFrame.""" 
        if self.everything_df is not None and not self.everything_df.empty:
            # Use .loc[] assignment instead of .update() to ensure values are set
            if symbol in self.everything_df.index:
                for col in update_df.columns:
                    if col in self.everything_df.columns:
                        old_value = self.everything_df.loc[symbol, col]
                        new_value = update_df.loc[symbol, col]
                        self.everything_df.loc[symbol, col] = new_value
                        # DEBUG: Log first update to confirm write
                        if self.connection_stats['messages_processed'] <= 3 and col in ['bid', 'ask', 'last']:
                            logger.info(f"DataFrame UPDATE: {symbol} {col}: {old_value} → {new_value}")
            else:
                logger.warning(f"Symbol '{symbol}' not found in everything_df.index. Index has {len(self.everything_df.index)} symbols.")
        else:
            logger.warning(f"Securities DataFrame not initialized for symbol: {symbol}")
    
    def _handle_processing_error(self, error: Exception, message: Dict[str, Any]):
        """Handle errors during message processing."""
        self.connection_stats['errors'] += 1
        
        error_context = {
            'error': str(error),
            'message_type': type(message).__name__,
            'has_symbol': 'instrumentId' in message if isinstance(message, dict) else 'unknown',
            'symbol': message.get('instrumentId', {}).get('symbol', 'unknown') if isinstance(message, dict) else 'unknown',
            'timestamp': datetime.now().isoformat()
        }
        
        logger.error(f"Error processing market data: {error}")
        logger.error(f"Context: Symbol={error_context['symbol']}, Type={error_context['message_type']}")
        logger.info("Continuing with processing of other messages - non-critical error")
        
        # Log detailed error for debugging
        if hasattr(error, '__traceback__'):
            import traceback
            logger.debug(f"Technical details: {traceback.format_exc()}")
    
    def websocket_error_handler(self, error):
        """Handle WebSocket error messages."""
        self.connection_stats['errors'] += 1
        log_connection_event("WebSocket Error", str(error))
        
        logger.error(f"WebSocket error: {error}")
        
        # Handle different types of errors
        if "authentication" in str(error).lower():
            logger.error("Authentication error - check credentials")
        elif "connection" in str(error).lower():
            logger.error("Connection error - check network connectivity")
        elif "product" in str(error['description']).lower():
            logger.error("Product error - " + error['description'])
        else:
            logger.error("Unknown WebSocket error")
    
    def websocket_exception_handler(self, exception):
        """Handle WebSocket exceptions."""
        self.connection_stats['errors'] += 1
        log_connection_event("WebSocket Exception", str(exception))
        
        logger.error(f"WebSocket exception: {exception}")
        
        # Log exception details
        if hasattr(exception, '__traceback__'):
            import traceback
            logger.debug(f"Exception traceback: {traceback.format_exc()}")
    
    def on_error(self, online, error):
        """Handle general errors."""
        self.connection_stats['errors'] += 1
        log_connection_event("General Error", f"Online: {online}, Error: {error}")
        
        logger.error(f"General error - Online: {online}, Error: {error}")
    
    def get_connection_stats(self) -> Dict[str, Any]:
        """Get connection statistics."""
        stats = self.connection_stats.copy()
        
        # Add calculated fields
        if stats['connection_start']:
            uptime = datetime.now() - stats['connection_start']
            stats['uptime_seconds'] = uptime.total_seconds()
        else:
            stats['uptime_seconds'] = 0
        
        # Calculate error rate
        total_messages = stats['messages_received']
        if total_messages > 0:
            stats['error_rate'] = stats['errors'] / total_messages
            stats['success_rate'] = stats['messages_processed'] / total_messages
        else:
            stats['error_rate'] = 0.0
            stats['success_rate'] = 0.0
        
        return stats
    
    def reset_stats(self):
        """Reset connection statistics."""
        self.connection_stats = {
            'messages_received': 0,
            'messages_processed': 0,
            'errors': 0,
            'last_message_time': None,
            'connection_start': datetime.now()
        }