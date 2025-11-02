"""
Execution Fetcher Module

Fetches filled/partially-filled executions from pyRofex API.
Supports both real-time WebSocket subscriptions and REST backfill.
"""

from datetime import datetime, timedelta, timezone
from queue import Queue
from typing import Callable, Dict, List, Optional

import pyRofex

from ..utils.logging import get_logger

logger = get_logger(__name__)


class ExecutionFetcher:
    """Fetches executions from pyRofex API."""
    
    def __init__(self, api_client):
        """
        Initialize execution fetcher.
        
        Args:
            api_client: pyRofexClient instance (from market_data.api_client)
        """
        self.api_client = api_client
        self.execution_queue = Queue()
        self._handler_registered = False
    
    def subscribe_order_reports(self, callback: Optional[Callable] = None):
        """
        Subscribe to real-time order reports via WebSocket.
        
        Args:
            callback: Optional callback function for processing executions
        """
        if not self.api_client.is_initialized:
            raise RuntimeError("API client not initialized")
        
        # Define handlers
        def order_report_handler(message):
            try:
                execution = self._parse_order_report(message)
                if execution:
                    if callback:
                        callback(execution)
                    else:
                        self.execution_queue.put(execution)
            except Exception as e:
                logger.error(f"Error in order report handler: {e}", exc_info=True)
        
        def error_handler(message):
            logger.error(f"WebSocket order report error: {message}")
        
        def exception_handler(exception):
            logger.error(f"WebSocket order report exception: {exception}", exc_info=True)
        
        # Initialize WebSocket connection with handlers
        pyRofex.init_websocket_connection(
            order_report_handler=order_report_handler,
            error_handler=error_handler,
            exception_handler=exception_handler
        )
        self._handler_registered = True
        
        # Subscribe
        pyRofex.order_report_subscription()
        logger.info("Subscribed to order reports with error handling")
    
    def fetch_historical_executions(self, from_date: datetime, to_date: Optional[datetime] = None, 
                                   batch_size: int = 500) -> List[Dict]:
        """
        Fetch historical executions via REST API.
        
        Args:
            from_date: Start date (UTC)
            to_date: End date (UTC), defaults to now
            batch_size: Max executions per batch
            
        Returns:
            List of execution dicts
        """
        if to_date is None:
            to_date = datetime.now(timezone.utc)
        
        try:
            # Call pyRofex REST API to get orders
            # Note: pyRofex may not have direct get_all_orders with date range
            # Using get_order_status per order if order IDs are available
            # For now, return empty list - this needs actual pyRofex API exploration
            logger.warning("Historical backfill not yet fully implemented - requires pyRofex API exploration")
            return []
            
        except Exception as e:
            logger.error(f"Error fetching historical executions: {e}", exc_info=True)
            return []
    
    def fetch_filled_orders_at_startup(self) -> List[Dict]:
        """
        Fetch all currently filled/partially filled orders at application startup.
        
        Uses REST API endpoint: GET /rest/order/filleds
        
        Returns:
            List of execution dicts ready for processing
        """
        try:
            logger.debug("Fetching filled orders at startup...")
            
            # Call API client to get filled orders
            response = self.api_client.get_filled_orders()
            
            if not response or response.get('status') != 'OK':
                logger.debug("No filled orders retrieved or request failed")
                return []
            
            orders = response.get('orders', [])
            
            if not orders:
                logger.debug("No filled orders found")
                return []
            
            # Parse each order into execution dict format
            executions = []
            for order in orders:
                execution = self._parse_filled_order(order)
                if execution:
                    executions.append(execution)
            
            logger.debug(f"Parsed {len(executions)} filled orders at startup")
            return executions
            
        except Exception as e:
            logger.error(f"Error fetching filled orders at startup: {e}", exc_info=True)
            return []
    
    def _parse_filled_order(self, order: Dict) -> Optional[Dict]:
        """
        Parse filled order from REST API into execution dict.
        
        REST API format:
        {
            'orderId': str,
            'clOrdId': str,
            'execId': str,
            'accountId': {'id': str},
            'instrumentId': {'marketId': str, 'symbol': str},
            'price': float,
            'orderQty': int,
            'ordType': str,
            'side': str,
            'timeInForce': str,
            'transactTime': str (format: YYYYMMDD-HH:MM:SS),
            'avgPx': float,
            'lastPx': float,
            'lastQty': int,
            'cumQty': int,
            'leavesQty': int,
            'status': str,
            'text': str
        }
        
        Args:
            order: Order dict from REST API response
            
        Returns:
            Execution dict or None if invalid
        """
        try:
            # Filter: only process filled/partially filled orders
            status = order.get('status')
            if status not in ['FILLED', 'PARTIALLY_FILLED']:
                logger.debug(f"Skipping order with status: {status}")
                return None
            
            # Extract execution data
            account_id = order.get('accountId', {})
            if isinstance(account_id, dict):
                account = account_id.get('id', '')
            else:
                account = str(account_id)
            
            instrument_id = order.get('instrumentId', {})
            symbol = instrument_id.get('symbol', '') if isinstance(instrument_id, dict) else ''
            
            execution = {
                'ExecutionID': order.get('execId', ''),
                'OrderID': order.get('orderId', ''),
                'Account': account,
                'Symbol': symbol,
                'Side': order.get('side', ''),
                'Quantity': order.get('orderQty', 0),
                'Price': order.get('price', 0.0),
                'FilledQty': order.get('cumQty', 0),
                'LastQty': order.get('lastQty', 0),
                'LastPx': order.get('lastPx', 0.0),
                'TimestampUTC': order.get('transactTime', ''),
                'Status': status,
                'ExecutionType': order.get('ordType', 'LIMIT'),
                'Source': 'pyRofex_REST'
            }
            
            # Validate required fields
            required = ['OrderID', 'Account', 'Symbol', 'Side', 'Quantity', 
                       'FilledQty', 'TimestampUTC']
            missing = [f for f in required if not execution.get(f)]
            if missing:
                logger.error(f"Missing required fields in filled order: {missing}")
                return None
            
            # Fallback for missing ExecutionID
            if not execution['ExecutionID']:
                execution['ExecutionID'] = f"{execution['OrderID']}_{execution['TimestampUTC']}_{execution['Account']}"
                logger.warning(f"Using fallback ExecutionID: {execution['ExecutionID']}")
            
            return execution
            
        except Exception as e:
            logger.error(f"Error parsing filled order: {e}", exc_info=True)
            return None
    
    def _parse_order_report(self, message: Dict) -> Optional[Dict]:
        """
        Parse order report message into execution dict.
        
        Args:
            message: Raw order report from pyRofex WebSocket
            
        Returns:
            Execution dict or None if invalid
        """
        if message.get('type') != 'orderReport':
            return None
        
        order_report = message.get('orderReport')
        if not order_report:
            logger.error("Missing orderReport in message")
            return None
        
        # Filter: only process filled/partially filled orders
        status = order_report.get('ordStatus')
        if status not in ['FILLED', 'PARTIALLY_FILLED']:
            logger.debug(f"Skipping order with status: {status}")
            return None
        
        # Extract execution data
        execution = {
            'ExecutionID': order_report.get('execId', ''),
            'OrderID': order_report.get('orderId'),
            'Account': order_report.get('account'),
            'Symbol': order_report.get('instrumentId', {}).get('symbol'),
            'Side': order_report.get('side'),
            'Quantity': order_report.get('orderQty'),
            'Price': order_report.get('price'),
            'FilledQty': order_report.get('cumQty'),
            'LastQty': order_report.get('lastQty'),
            'LastPx': order_report.get('lastPx'),
            'TimestampUTC': order_report.get('transactTime'),
            'Status': status,
            'ExecutionType': order_report.get('execType'),
            'Source': 'pyRofex'
        }
        
        # Validate required fields
        required = ['OrderID', 'Account', 'Symbol', 'Side', 'Quantity', 
                   'FilledQty', 'TimestampUTC']
        missing = [f for f in required if not execution.get(f)]
        if missing:
            logger.error(f"Missing required fields: {missing}")
            return None
        
        # Fallback for missing ExecutionID
        if not execution['ExecutionID']:
            execution['ExecutionID'] = f"{execution['OrderID']}_{execution['TimestampUTC']}_{execution['Account']}"
            logger.warning(f"Using fallback ExecutionID: {execution['ExecutionID']}")
        
        return execution
