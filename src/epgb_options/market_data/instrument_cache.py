"""
Instrument cache for EPGB Options.

This module handles caching of available instruments from pyRofex
with TTL (time-to-live) functionality.
"""

import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Set

from ..utils.logging import get_logger

logger = get_logger(__name__)


class InstrumentCache:
    """Manages caching of available instruments with TTL."""
    
    def __init__(self, cache_dir: Optional[Path] = None, ttl_minutes: int = 30):
        """
        Initialize instrument cache.
        
        Args:
            cache_dir: Directory to store cache files (defaults to data/cache)
            ttl_minutes: Time-to-live in minutes (default: 30)
        """
        if cache_dir is None:
            # Default to data/cache directory
            self.cache_dir = Path(__file__).resolve().parents[3] / 'data' / 'cache'
        else:
            self.cache_dir = cache_dir
        
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.cache_file = self.cache_dir / 'instruments_cache.json'
        self.ttl_minutes = ttl_minutes
        
        logger.info(f"Instrument cache initialized: {self.cache_file} (TTL: {ttl_minutes}m)")
    
    def get_cached_instruments(self) -> Optional[Dict[str, any]]:
        """
        Get cached instruments if valid (not expired).
        
        Returns:
            Dict with instruments data or None if cache is invalid/expired
        """
        try:
            if not self.cache_file.exists():
                logger.info("No instrument cache found")
                return None
            
            # Read cache file
            with open(self.cache_file, 'r', encoding='utf-8') as f:
                cache_data = json.load(f)
            
            # Check cache timestamp
            cached_time = datetime.fromisoformat(cache_data.get('timestamp', ''))
            age = datetime.now() - cached_time
            
            if age > timedelta(minutes=self.ttl_minutes):
                logger.info(f"Instrument cache expired (age: {age.total_seconds()/60:.1f}m > TTL: {self.ttl_minutes}m)")
                return None
            
            logger.info(f"Using cached instruments (age: {age.total_seconds()/60:.1f}m, {len(cache_data.get('instruments', []))} instruments)")
            return cache_data
            
        except Exception as e:
            logger.error(f"Error reading instrument cache: {e}")
            return None
    
    def save_instruments(self, instruments: List[Dict], metadata: Optional[Dict] = None):
        """
        Save instruments to cache.
        
        Args:
            instruments: List of instrument dictionaries from pyRofex
            metadata: Optional metadata to store with cache
        """
        try:
            cache_data = {
                'timestamp': datetime.now().isoformat(),
                'ttl_minutes': self.ttl_minutes,
                'instruments': instruments,
                'count': len(instruments),
                'metadata': metadata or {}
            }
            
            # Write to cache file
            with open(self.cache_file, 'w', encoding='utf-8') as f:
                json.dump(cache_data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Saved {len(instruments)} instruments to cache: {self.cache_file}")
            
        except Exception as e:
            logger.error(f"Error saving instrument cache: {e}")
    
    def get_instrument_symbols(self) -> Set[str]:
        """
        Get set of valid instrument symbols from cache.
        
        Returns:
            Set of instrument symbols (tickers)
        """
        cache_data = self.get_cached_instruments()
        if not cache_data:
            return set()
        
        instruments = cache_data.get('instruments', [])
        # Extract symbols/tickers from instruments
        symbols = set()
        for instrument in instruments:
            # Handle different instrument formats
            if isinstance(instrument, str):
                # Already a symbol string
                symbols.add(instrument)
            elif isinstance(instrument, dict):
                # pyRofex instruments have 'symbol' or 'instrumentId' field
                symbol = instrument.get('symbol') or instrument.get('instrumentId', {}).get('symbol')
                if symbol:
                    symbols.add(symbol)
        
        return symbols
    
    def is_valid_instrument(self, symbol: str) -> bool:
        """
        Check if symbol is a valid instrument.
        
        Args:
            symbol: Symbol to validate
            
        Returns:
            True if symbol exists in cached instruments
        """
        valid_symbols = self.get_instrument_symbols()
        return symbol in valid_symbols
    
    def clear_cache(self):
        """Clear the instrument cache."""
        try:
            if self.cache_file.exists():
                self.cache_file.unlink()
                logger.info("Instrument cache cleared")
        except Exception as e:
            logger.error(f"Error clearing cache: {e}")
