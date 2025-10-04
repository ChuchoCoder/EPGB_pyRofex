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
        
        logger.info(f"Caché de instrumentos inicializado: {self.cache_file} (TTL: {self.ttl_minutes}m)")
        logger.info("Usando caché multi-nivel: Memoria → Archivo → API")
    
    def _is_memory_cache_valid(self) -> bool:
        """Verifica si el caché en memoria sigue siendo válido (no expirado)."""
        if self._memory_cache is None or self._memory_cache_timestamp is None:
            return False
        
        age = datetime.now() - self._memory_cache_timestamp
        return age <= timedelta(minutes=self.ttl_minutes)
    
    def _build_lookups(self, cache_data: Dict):
        """
        Construye estructuras de búsqueda rápidas a partir de los datos de caché.
        
        Args:
            cache_data: Datos de caché que contienen la lista de instrumentos
        """
        instruments = cache_data.get('instruments', [])
        
        # Construir mapping símbolo → instrumento para búsquedas O(1)
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
        
        logger.debug(f"Estructuras de búsqueda construidas: {len(self._all_symbols)} símbolos, {len(self._options_symbols)} opciones")
    
    def get_cached_instruments(self) -> Optional[Dict[str, any]]:
        """
        Obtener instrumentos en caché si son válidos (no expirados).
        
        Usa caché multi-nivel:
        1. Memoria (más rápido)
        2. Archivo (si memoria expiró)
        3. Retorna None si ambos expiraron (el caller debe obtenerlos de la API)
        
        Returns:
            Dict con datos de instrumentos o None si el caché es inválido/expirado
        """
        # NIVEL 1: Verificar primero el caché en memoria (más rápido)
        if self._is_memory_cache_valid():
            logger.debug("✓ Usando caché en MEMORIA (Nivel 1)")
            return self._memory_cache
        
        # NIVEL 2: Check file cache
        try:
            if not self.cache_file.exists():
                logger.debug("✗ No se encontró caché en archivo (Nivel 2)")
                return None
            
            # Leer archivo de caché
            with open(self.cache_file, 'r', encoding='utf-8') as f:
                cache_data = json.load(f)
            
            # Check cache timestamp
            cached_time = datetime.fromisoformat(cache_data.get('timestamp', ''))
            age = datetime.now() - cached_time
            
            if age > timedelta(minutes=self.ttl_minutes):
                logger.info(f"✗ Caché en archivo expirado (edad: {age.total_seconds()/60:.1f}m > TTL: {self.ttl_minutes}m)")
                return None
            
            # File cache is valid - load into memory cache
            logger.info(f"✓ Usando caché de ARCHIVO (Nivel 2) - cargando en memoria (edad: {age.total_seconds()/60:.1f}m, {len(cache_data.get('instruments', []))} instrumentos)")
            self._memory_cache = cache_data
            self._memory_cache_timestamp = datetime.now()
            
            # Build fast lookup structures
            self._build_lookups(cache_data)
            
            return cache_data
            
        except Exception as e:
            logger.error(f"Error leyendo caché de instrumentos: {e}")
            return None
    
    def save_instruments(self, instruments: List[Dict], metadata: Optional[Dict] = None):
        """
        Guarda instrumentos en caché (memoria y archivo).
        
        Args:
            instruments: Lista de diccionarios de instrumentos desde pyRofex
            metadata: Metadata opcional para almacenar con el caché
        """
        try:
            cache_data = {
                'timestamp': datetime.now().isoformat(),
                'ttl_minutes': self.ttl_minutes,
                'instruments': instruments,
                'count': len(instruments),
                'metadata': metadata or {}
            }
            
            # Guardar en caché de MEMORIA (Nivel 1)
            self._memory_cache = cache_data
            self._memory_cache_timestamp = datetime.now()
            
            # Construir estructuras de búsqueda rápidas
            self._build_lookups(cache_data)
            
            # Guardar en caché de ARCHIVO (Nivel 2)
            with open(self.cache_file, 'w', encoding='utf-8') as f:
                json.dump(cache_data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"✓ Guardados {len(instruments)} instrumentos en caché (MEMORIA + ARCHIVO)")
            
        except Exception as e:
            logger.error(f"Error guardando caché de instrumentos: {e}")
    
    def get_instrument_symbols(self) -> Set[str]:
        """
        Obtiene el set de símbolos válidos de instrumentos desde el caché.
        Usa estructuras pre-construidas para rendimiento O(1).
        
        Returns:
            Set de símbolos de instrumentos (tickers)
        """
        # Use pre-built lookup if available (memory cache loaded)
        if self._all_symbols is not None:
            return self._all_symbols
        
        # Reintento: construir desde datos de caché
        cache_data = self.get_cached_instruments()
        if not cache_data:
            return set()
        
        instruments = cache_data.get('instruments', [])
        # Extract symbols/tickers from instruments
        symbols = set()
        for instrument in instruments:
            # Handle different instrument formats
            if isinstance(instrument, str):
                # Ya es una cadena símbolo
                symbols.add(instrument)
            elif isinstance(instrument, dict):
                # Los instrumentos de pyRofex pueden tener 'symbol' o 'instrumentId'
                symbol = instrument.get('symbol') or instrument.get('instrumentId', {}).get('symbol')
                if symbol:
                    symbols.add(symbol)
        
        return symbols
    
    def is_valid_instrument(self, symbol: str) -> bool:
        """
        Verifica si un símbolo es un instrumento válido.
        
        Args:
            symbol: Símbolo a validar
            
        Returns:
            True si el símbolo existe en el caché de instrumentos
        """
        valid_symbols = self.get_instrument_symbols()
        return symbol in valid_symbols
    
    def get_instrument_by_symbol(self, symbol: str) -> Optional[Dict]:
        """
        Obtiene los datos completos de un instrumento para un símbolo específico.
        Usa lookup O(1) pre-construido para máximo rendimiento.
        
        Args:
            symbol: Símbolo a buscar
            
        Returns:
            Dict con los datos del instrumento o None si no se encontró
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
        Verifica si un símbolo representa una opción basado en su cficode.
        Usa lookup O(1) pre-construido para máximo rendimiento.
        
        Las opciones tienen cficode "OCASPS" (CALL) o "OPASPS" (PUT) según la API de pyRofex.
        Depende únicamente de los datos en caché - sin fallback por patrones.
        
        Args:
            symbol: Símbolo a chequear
            
        Returns:
            True si el símbolo es una opción
        """
        # Usar lookup O(1) pre-construido si está disponible (más rápido)
        if self._options_symbols is not None and len(self._options_symbols) > 0:
            return symbol in self._options_symbols
        
        # Fallback: Try to get instrument data from cache
        instrument = self.get_instrument_by_symbol(symbol)
        
        if instrument:
            # Verificar cficode - las opciones tienen "OCASPS" (CALL) o "OPASPS" (PUT)
            cficode = instrument.get('cficode', '')
            if cficode in ('OCASPS', 'OPASPS'):
                return True
        
        return False
    
    def get_options_symbols(self) -> Set[str]:
        """
        Obtiene el conjunto de todos los símbolos de opciones desde el caché.
        Usa lookup O(1) pre-construido para máximo rendimiento.
        
        Returns:
            Set de símbolos de opciones
        """
        # Use pre-built lookup if available (fastest)
        if self._options_symbols is not None:
            return self._options_symbols
        
        # Reintento: construir desde datos de caché
        cache_data = self.get_cached_instruments()
        if not cache_data:
            return set()
        
        instruments = cache_data.get('instruments', [])
        options_symbols = set()
        
        for instrument in instruments:
            if isinstance(instrument, dict):
                # Verificar si es una opción (CALL o PUT)
                cficode = instrument.get('cficode', '')
                if cficode in ('OCASPS', 'OPASPS'):
                    symbol = instrument.get('instrumentId', {}).get('symbol')
                    if symbol:
                        options_symbols.add(symbol)
        
        return options_symbols
    
    def clear_cache(self):
        """Limpia el caché en memoria y en archivo."""
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
                logger.info("✓ Caché LIMPIADO: MEMORIA + ARCHIVO")
            else:
                logger.info("✓ Caché LIMPIADO: MEMORIA")
        except Exception as e:
            logger.error(f"Error limpiando caché: {e}")
    
    def get_cache_stats(self) -> Dict[str, any]:
        """
        Obtiene estadísticas sobre el estado y rendimiento del caché.
        
        Returns:
            Dict con estadísticas del caché
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
