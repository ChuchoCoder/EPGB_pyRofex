"""
Trades Module

Provides execution fetching, processing, and upsert for Trades sheet.
"""

from .execution_fetcher import ExecutionFetcher
from .trades_processor import TradesProcessor
from .trades_upsert import TradesUpserter

__all__ = [
    'ExecutionFetcher',
    'TradesProcessor',
    'TradesUpserter',
]
