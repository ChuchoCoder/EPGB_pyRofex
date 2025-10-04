"""
Caché de instrumentos para EPGB Options.

Este módulo maneja el almacenamiento en caché de instrumentos disponibles desde pyRofex
con funcionalidad TTL (tiempo de vida).
"""

import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Set

from ..utils.logging import get_logger

logger = get_logger(__name__)


class InstrumentCache:
    """
    Administra el almacenamiento en caché de instrumentos disponibles con TTL.
    
    Usa estrategia de caché multi-nivel para rendimiento óptimo:
    1. Memory cache (más rápido) - en RAM
    2. File cache (rápido) - en disco
    3. API fetch (más lento) - desde pyRofex
    """
    
    def __init__(self, cache_dir: Optional[Path] = None, ttl_minutes: int = 30):
        """
        Inicializar caché de instrumentos.
        
        Args:
            cache_dir: Directorio para almacenar archivos de caché (por defecto data/cache)
            ttl_minutes: Tiempo de vida en minutos (por defecto: 30)
        """
        if cache_dir is None:
            # Por defecto al directorio data/cache
            self.cache_dir = Path(__file__).resolve().parents[3] / 'data' / 'cache'
        else:
            self.cache_dir = cache_dir
        
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.cache_file = self.cache_dir / 'instruments_cache.json'
        self.ttl_minutes = ttl_minutes
        
        # Memory cache - NIVEL 1 (más rápido)
        self._memory_cache: Optional[Dict] = None
        self._memory_cache_timestamp: Optional[datetime] = None
        
        # Pre-built lookups for fast access
        self._symbol_to_instrument: Dict[str, Dict] = {}
        self._options_symbols: Optional[Set[str]] = None
        self._all_symbols: Optional[Set[str]] = None
        
        logger.info(f"Caché de instrumentos inicializado: {self.cache_file} (TTL: {ttl_minutes}m)")
        logger.info("Usando caché multi-nivel: Memory → File → API")
    
    def _is_memory_cache_valid(self) -> bool:
        """Check if memory cache is still valid (not expired)."""
        if self._memory_cache is None or self._memory_cache_timestamp is None:
            return False
        
        age = datetime.now() - self._memory_cache_timestamp
        return age <= timedelta(minutes=self.ttl_minutes)
    
    def _build_lookups(self, cache_data: Dict):
        """
        Build fast lookup structures from cache data.
        
        Args:
            cache_data: Cache data with instruments list
        """
        instruments = cache_data.get('instruments', [])
        
        # Build symbol → instrument mapping for O(1) lookups
        self._symbol_to_instrument = {}
        self._options_symbols = set()
        self._all_symbols = set()
        
        for instrument in instruments:
            if isinstance(instrument, dict):
                symbol = instrument.get('instrumentId', {}).get('symbol')
                if symbol:
                    self._symbol_to_instrument[symbol] = instrument
                    self._all_symbols.add(symbol)
                    
                    # Pre-identify options (both CALL and PUT)
                    # OCASPS = CALL options, OPASPS = PUT options
                    cficode = instrument.get('cficode', '')
                    if cficode in ('OCASPS', 'OPASPS'):
                        self._options_symbols.add(symbol)
        
        logger.debug(f"Built lookups: {len(self._all_symbols)} symbols, {len(self._options_symbols)} options")
    
    def get_cached_instruments(self) -> Optional[Dict[str, any]]:
        """
        Obtener instrumentos en caché si son válidos (no expirados).
        
        Usa caché multi-nivel:
        1. Memory cache (más rápido)
        2. File cache (si memory expiró)
        3. Return None si ambos expiraron (caller debe obtener de API)
        
        Returns:
            Dict con datos de instrumentos o None si el caché es inválido/expirado
        """
        # NIVEL 1: Check memory cache first (fastest)
        if self._is_memory_cache_valid():
            logger.debug("✓ Using MEMORY cache (Level 1)")
            return self._memory_cache
        
        # NIVEL 2: Check file cache
        try:
            if not self.cache_file.exists():
                logger.debug("✗ No file cache found (Level 2)")
                return None
            
            # Read cache file
            with open(self.cache_file, 'r', encoding='utf-8') as f:
                cache_data = json.load(f)
            
            # Check cache timestamp
            cached_time = datetime.fromisoformat(cache_data.get('timestamp', ''))
            age = datetime.now() - cached_time
            
            if age > timedelta(minutes=self.ttl_minutes):
                logger.info(f"✗ File cache expired (age: {age.total_seconds()/60:.1f}m > TTL: {self.ttl_minutes}m)")
                return None
            
            # File cache is valid - load into memory cache
            logger.info(f"✓ Using FILE cache (Level 2) - loading to memory (age: {age.total_seconds()/60:.1f}m, {len(cache_data.get('instruments', []))} instruments)")
            self._memory_cache = cache_data
            self._memory_cache_timestamp = datetime.now()
            
            # Build fast lookup structures
            self._build_lookups(cache_data)
            
            return cache_data
            
        except Exception as e:
            logger.error(f"Error reading instrument cache: {e}")
            return None
    
    def save_instruments(self, instruments: List[Dict], metadata: Optional[Dict] = None):
        """
        Save instruments to cache (both memory and file).
        
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
            
            # Save to MEMORY cache (Level 1)
            self._memory_cache = cache_data
            self._memory_cache_timestamp = datetime.now()
            
            # Build fast lookup structures
            self._build_lookups(cache_data)
            
            # Save to FILE cache (Level 2)
            with open(self.cache_file, 'w', encoding='utf-8') as f:
                json.dump(cache_data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"✓ Saved {len(instruments)} instruments to MEMORY + FILE cache")
            
        except Exception as e:
            logger.error(f"Error saving instrument cache: {e}")
    
    def get_instrument_symbols(self) -> Set[str]:
        """
        Get set of valid instrument symbols from cache.
        Uses pre-built lookup for O(1) performance.
        
        Returns:
            Set of instrument symbols (tickers)
        """
        # Use pre-built lookup if available (memory cache loaded)
        if self._all_symbols is not None:
            return self._all_symbols
        
        # Fallback to building from cache data
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
    
    def get_instrument_by_symbol(self, symbol: str) -> Optional[Dict]:
        """
        Get full instrument data for a specific symbol.
        Uses pre-built O(1) lookup for maximum performance.
        
        Args:
            symbol: Symbol to look up
            
        Returns:
            Dict with instrument data or None if not found
        """
        # Use pre-built O(1) lookup if available (memory cache loaded)
        if self._symbol_to_instrument:
            return self._symbol_to_instrument.get(symbol)
        
        # Fallback to linear search in cache data
        cache_data = self.get_cached_instruments()
        if not cache_data:
            return None
        
        instruments = cache_data.get('instruments', [])
        for instrument in instruments:
            if isinstance(instrument, dict):
                inst_symbol = instrument.get('instrumentId', {}).get('symbol')
                if inst_symbol == symbol:
                    return instrument
        
        return None
    
    def is_option_symbol(self, symbol: str) -> bool:
        """
        Check if symbol represents an option based on cficode.
        Uses pre-built O(1) lookup for maximum performance.
        
        Options have cficode "OCASPS" (CALL) or "OPASPS" (PUT) according to pyRofex API.
        Relies solely on cache data - no pattern matching fallback.
        
        Args:
            symbol: Symbol to check
            
        Returns:
            True if symbol is an option
        """
        # Use pre-built O(1) lookup if available (fastest)
        if self._options_symbols is not None and len(self._options_symbols) > 0:
            return symbol in self._options_symbols
        
        # Fallback: Try to get instrument data from cache
        instrument = self.get_instrument_by_symbol(symbol)
        
        if instrument:
            # Check cficode - options have "OCASPS" (CALL) or "OPASPS" (PUT)
            cficode = instrument.get('cficode', '')
            if cficode in ('OCASPS', 'OPASPS'):
                return True
        
        return False
    
    def get_options_symbols(self) -> Set[str]:
        """
        Get set of all option symbols from cache.
        Uses pre-built O(1) lookup for maximum performance.
        
        Returns:
            Set of option symbols
        """
        # Use pre-built lookup if available (fastest)
        if self._options_symbols is not None:
            return self._options_symbols
        
        # Fallback to building from cache data
        cache_data = self.get_cached_instruments()
        if not cache_data:
            return set()
        
        instruments = cache_data.get('instruments', [])
        options_symbols = set()
        
        for instrument in instruments:
            if isinstance(instrument, dict):
                # Check if it's an option (CALL or PUT)
                cficode = instrument.get('cficode', '')
                if cficode in ('OCASPS', 'OPASPS'):
                    symbol = instrument.get('instrumentId', {}).get('symbol')
                    if symbol:
                        options_symbols.add(symbol)
        
        return options_symbols
    
    def clear_cache(self):
        """Clear both memory and file cache."""
        try:
            # Clear memory cache
            self._memory_cache = None
            self._memory_cache_timestamp = None
            self._symbol_to_instrument.clear()
            self._options_symbols = None
            self._all_symbols = None
            
            # Clear file cache
            if self.cache_file.exists():
                self.cache_file.unlink()
                logger.info("✓ Cleared MEMORY + FILE cache")
            else:
                logger.info("✓ Cleared MEMORY cache")
        except Exception as e:
            logger.error(f"Error clearing cache: {e}")
    
    def get_cache_stats(self) -> Dict[str, any]:
        """
        Get statistics about cache state and performance.
        
        Returns:
            Dict with cache statistics
        """
        stats = {
            'memory_cache_active': self._memory_cache is not None,
            'memory_cache_valid': self._is_memory_cache_valid(),
            'file_cache_exists': self.cache_file.exists(),
            'ttl_minutes': self.ttl_minutes,
            'total_instruments': len(self._symbol_to_instrument) if self._symbol_to_instrument else 0,
            'total_options': len(self._options_symbols) if self._options_symbols else 0,
            'lookup_structures_built': bool(self._symbol_to_instrument)
        }
        
        if self._memory_cache_timestamp:
            age = datetime.now() - self._memory_cache_timestamp
            stats['memory_cache_age_seconds'] = age.total_seconds()
            stats['memory_cache_age_minutes'] = age.total_seconds() / 60
        
        return stats
