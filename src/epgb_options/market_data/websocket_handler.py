"""
Manejador de WebSocket para EPGB Options.

Este módulo maneja conexiones de WebSocket, procesamiento de mensajes y manejo de errores
para datos de mercado en tiempo real desde pyRofex.
"""

from datetime import datetime
from typing import Any, Callable, Dict, Optional

import pandas as pd

from ..utils.helpers import get_excel_safe_value
from ..utils.logging import (get_logger, log_connection_event,
                             log_market_data_event)
from ..utils.progress_logger import ProgressLogger, SummaryLogger
from ..utils.validation import (safe_float_conversion, safe_int_conversion,
                                validate_market_data)
from .instrument_cache import InstrumentCache

logger = get_logger(__name__)


class WebSocketHandler:
    """Maneja conexiones de WebSocket y el procesamiento de mensajes."""
    
    def __init__(self, instrument_cache: Optional[InstrumentCache] = None):
        """
        Inicializar manejador de WebSocket.
        
        Args:
            instrument_cache: Instancia opcional de InstrumentCache para clasificación precisa de instrumentos
        """
        self.is_connected = False
        self.connection_stats = {
            'messages_received': 0,
            'messages_processed': 0, 
            'errors': 0,
            'last_message_time': None,
            'connection_start': None
        }
        
        # Referencias de almacenamiento de datos (serán configuradas por la aplicación principal)
        self.options_df = None
        self.everything_df = None
        self.cauciones_df = None
        
        # Instrument cache for classification
        self.instrument_cache = instrument_cache or InstrumentCache()
        
        # Callbacks
        self.on_data_update = None  # Callback para cuando los datos se actualizan
        
        # Progress and summary loggers
        self._progress_logger = ProgressLogger(throttle_seconds=1.0)
        self._summary_logger = SummaryLogger(logger, interval_seconds=30.0)
    
    def set_data_references(self, options_df: pd.DataFrame, everything_df: pd.DataFrame, cauciones_df: pd.DataFrame = None):
        """Configurar referencias a los DataFrames principales."""
        self.options_df = options_df
        self.everything_df = everything_df
        self.cauciones_df = cauciones_df if cauciones_df is not None else pd.DataFrame()
    
    def set_update_callback(self, callback: Callable):
        """Configurar función de callback para actualizaciones de datos."""
        self.on_data_update = callback
    
    def market_data_handler(self, message: Dict[str, Any]):
        """
        Manejar mensajes de datos de mercado desde el WebSocket de pyRofex.
        
        Estructura esperada del mensaje de pyRofex:
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
            message: Mensaje de datos de mercado desde pyRofex
        """
        self.connection_stats['messages_received'] += 1
        self.connection_stats['last_message_time'] = datetime.now()
        
        # DEBUG: Log raw message structure for first few messages
        if self.connection_stats['messages_received'] <= 3:
            logger.debug(f"MENSAJE CRUDO #{self.connection_stats['messages_received']}: {message}")
        
        try:
            # Validate message structure
            if not validate_market_data(message):
                logger.warning(f"Mensaje de datos de mercado inválido: {message}")
                self.connection_stats['errors'] += 1
                return
            
            # Extract symbol (safe access with 'or {}' to handle None instrumentId)
            instrument_id = message.get('instrumentId') or {}
            symbol = instrument_id.get('symbol')
            if not symbol:
                logger.warning("No hay símbolo en el mensaje de datos de mercado")
                return
            
            # Process market data
            self._process_market_data(symbol, message)
            self.connection_stats['messages_processed'] += 1
            
            # Update summary statistics
            self._summary_logger.increment('messages_processed')
            self._summary_logger.set_stat('last_symbol', symbol[:30])  # Truncate long symbols
            
            # Show progress - DISABLED: unified status line in main.py handles this
            # timestamp = datetime.now().strftime("%H:%M:%S")
            # self._progress_logger.update(
            #     f"📡 WS [{timestamp}]: {self.connection_stats['messages_received']} msgs | "
            #     f"{self.connection_stats['messages_processed']} OK | "
            #     f"{self.connection_stats['errors']} err | "
            #     f"Último: {symbol[:25]}"
            # )
            
            # Show periodic summary - DISABLED: unified status line in main.py handles this
            # self._summary_logger.show_summary("WebSocket Stats")
            
            # DEBUG level for individual message details (TEMPORARILY DISABLED due to caching issues)
            # market_data = message.get('marketData') or {}
            # logger.debug(f"Procesado {symbol}: last={market_data.get('LA', {}).get('price', 'N/A')}")
            
            # Notify callback if set
            if self.on_data_update:
                try:
                    self.on_data_update(symbol, message)
                except Exception as e:
                    logger.error(f"Error en callback de actualización: {e}")
        
        except Exception as e:
            self._handle_processing_error(e, message)
    
    def _process_market_data(self, symbol: str, message: Dict[str, Any]):
        """Procesar datos de mercado y actualizar el DataFrame correspondiente."""
        
        # Extract market data fields
        market_data = message.get('marketData')
        
        # Validate that marketData exists and is not None
        if market_data is None:
            logger.debug(f"Mensaje sin datos de mercado para {symbol} - omitiendo")
            return
        
        # DEBUG: Log market data extraction for first symbol
        if self.connection_stats['messages_processed'] < 2:
            logger.debug(f"Procesando símbolo: {symbol}")
            logger.debug(f"Campos de datos de mercado: {market_data}")

        # Extracción de campos anidados (pyRofex 0.5.0 usa estructuras anidadas)
        # Mapeo de campos del mensaje de WebSocket de pyRofex:
        # BI = BIDS (array de {price, size})
        # OF = OFFERS (array de {price, size})
        # LA = LAST trade ({price, size, date})
        # OP = OPENING_PRICE (número o {price})
        # CL = CLOSING_PRICE (número o {price})
        # HI = HIGH_PRICE (número o {price})
        # LO = LOW_PRICE (número o {price})
        # EV = TRADE_EFFECTIVE_VOLUME (número) -> columna turnover
        # NV = NOMINAL_VOLUME (número) -> columna volume
        # TC = TRADE_COUNT (número) -> columna operations (cantidad de operaciones)
        # SE = SETTLEMENT_PRICE (número o {price})
        # OI = OPEN_INTEREST (número)

        bids = market_data.get('BI', [])
        offers = market_data.get('OF', [])
        last_trade = market_data.get('LA', {})

        # Extract best bid/offer (first level in the book)
        best_bid = bids[0] if bids and isinstance(bids, list) else {}
        best_offer = offers[0] if offers and isinstance(offers, list) else {}

        # Helper function to extract price from either number or dict
        def extract_price(value):
            if isinstance(value, dict):
                return safe_float_conversion(value.get('price'))
            return safe_float_conversion(value)

        # Extract key prices for change calculation
        last_price = safe_float_conversion(last_trade.get('price') if isinstance(last_trade, dict) else None)
        previous_close = extract_price(market_data.get('CL'))

        # Calculate change percentage: (last / previous_close) - 1
        change = 0.0
        if last_price and previous_close and previous_close != 0:
            change = ((last_price / previous_close) - 1)

        # Create data row compatible with existing Excel structure
        data_row = {
            'bid_size': safe_int_conversion(best_bid.get('size') if isinstance(best_bid, dict) else None),
            'bid': safe_float_conversion(best_bid.get('price') if isinstance(best_bid, dict) else None),
            'ask': safe_float_conversion(best_offer.get('price') if isinstance(best_offer, dict) else None),
            'ask_size': safe_int_conversion(best_offer.get('size') if isinstance(best_offer, dict) else None),
            'last': last_price,
            'change': change,
            'open': extract_price(market_data.get('OP')),
            'high': extract_price(market_data.get('HI')),
            'low': extract_price(market_data.get('LO')),
            'previous_close': previous_close,
            'turnover': safe_float_conversion(market_data.get('EV')),      # TRADE_EFFECTIVE_VOLUME
            'volume': safe_int_conversion(market_data.get('NV')),          # NOMINAL_VOLUME
            'operations': safe_int_conversion(market_data.get('TC')),      # TRADE_COUNT
            'datetime': pd.Timestamp.now()
        }

        # DEBUG: Registrar valores extraídos
        if self.connection_stats['messages_processed'] < 2:
            logger.debug(f"Fila de datos extraída: {data_row}")

        # Create DataFrame for this update
        update_df = pd.DataFrame([data_row], index=[symbol])

        # Determine which DataFrame to update based on symbol characteristics
        if self._is_options_symbol(symbol):
            self._update_options_data(symbol, update_df)
        elif self._is_caucion_symbol(symbol):
            self._update_cauciones_data(symbol, update_df)
        elif self._is_futures_symbol(symbol):
            # Futures are in everything_df but log separately for clarity
            self._update_securities_data(symbol, update_df)
            logger.debug(f"Futuro actualizado {symbol}: last={data_row['last']}, bid={data_row['bid']}, ask={data_row['ask']}")
        else:
            self._update_securities_data(symbol, update_df)

        # Use DEBUG for individual updates (too verbose for INFO)
        logger.debug(f"Actualizado {symbol}: last={data_row['last']}, bid={data_row['bid']}, ask={data_row['ask']}")
    
    def _is_options_symbol(self, symbol: str) -> bool:
        """
        Determina si el símbolo representa un contrato de opción.
        
        Usa InstrumentCache para una clasificación precisa basada en cficode.
        Si no hay cache disponible, cae en una comprobación por patrón.
        
        Args:
            symbol: Símbolo a verificar
            
        Returns:
            True si el símbolo es una opción
        """
        return self.instrument_cache.is_option_symbol(symbol)
    
    def _is_caucion_symbol(self, symbol: str) -> bool:
        """Determina si el símbolo representa una caución (repo)."""
        # Las cauciones tienen formato "MERV - XMEV - PESOS - XD" donde X es la cantidad de días
        return 'PESOS' in symbol and symbol.split(' - ')[-1].endswith('D')
    
    def _is_futures_symbol(self, symbol: str) -> bool:
        """
        Determina si el símbolo representa un contrato de futuro.
        
        Los futuros se identifican por tener "/" en el símbolo (fecha de vencimiento)
        y no contener "PESOS" (para distinguirlos de las cauciones).
        
        Args:
            symbol: Símbolo a verificar
            
        Returns:
            True si el símbolo es un futuro
            
        Examples:
            - "DLR/FEB26" → True (futuro de dólar)
            - "DLR/NOV25" → True (futuro de dólar)
            - "MAI.ROS/MAR26" → True (futuro de maíz ROS)
            - "ORO/ENE26" → True (futuro de oro)
            - "MERV - XMEV - GGAL - 24hs" → False (acción)
            - "MERV - XMEV - PESOS - 3D" → False (caución)
        """
        return '/' in symbol and 'PESOS' not in symbol
    
    def _update_options_data(self, symbol: str, update_df: pd.DataFrame):
        """Actualizar el DataFrame de opciones."""
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
            logger.warning(f"DataFrame de opciones no inicializado para el símbolo: {symbol}")
    
    def _update_securities_data(self, symbol: str, update_df: pd.DataFrame):
        """Actualizar el DataFrame de valores (securities).""" 
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
                            logger.debug(f"DataFrame UPDATE: {symbol} {col}: {old_value} → {new_value}")
            else:
                logger.warning(f"Símbolo '{symbol}' no encontrado en everything_df.index. El índice tiene {len(self.everything_df.index)} símbolos.")
        else:
            logger.warning(f"DataFrame de valores no inicializado para el símbolo: {symbol}")
    
    def _update_cauciones_data(self, symbol: str, update_df: pd.DataFrame):
        """Actualizar DataFrame de cauciones (separado de la tabla principal de valores).""" 
        if self.cauciones_df is not None and not self.cauciones_df.empty:
            # Use .loc[] assignment instead of .update() to ensure values are set
            if symbol in self.cauciones_df.index:
                for col in update_df.columns:
                    if col in self.cauciones_df.columns:
                        self.cauciones_df.loc[symbol, col] = update_df.loc[symbol, col]
                logger.debug(f"Caución actualizada: {symbol}")
            else:
                logger.warning(f"Símbolo de caución '{symbol}' no encontrado en cauciones_df.index")
        else:
            logger.warning(f"DataFrame de cauciones no inicializado para el símbolo: {symbol}")
    
    def _handle_processing_error(self, error: Exception, message: Dict[str, Any]):
        """Manejar errores ocurridos durante el procesamiento de mensajes."""
        self.connection_stats['errors'] += 1
        
        # Safe extraction of symbol for error context
        instrument_id = message.get('instrumentId') or {} if isinstance(message, dict) else {}
        symbol = instrument_id.get('symbol', 'unknown')
        
        error_context = {
            'error': str(error),
            'message_type': type(message).__name__,
            'has_symbol': 'instrumentId' in message if isinstance(message, dict) else 'unknown',
            'symbol': symbol,
            'timestamp': datetime.now().isoformat()
        }
        logger.error(f"Error al procesar datos de mercado: {error}")
        logger.error(f"Contexto: Símbolo={error_context['symbol']}, Tipo={error_context['message_type']}")
        
        # Log detailed traceback at ERROR level (temporarily for debugging)
        if hasattr(error, '__traceback__'):
            import traceback
            logger.error(f"TRACEBACK COMPLETO:\n{traceback.format_exc()}")
        
        logger.info("Continuando con el procesamiento de otros mensajes - error no crítico")
    
    def websocket_error_handler(self, error):
        """Manejar mensajes de error del WebSocket."""
        try:
            self.connection_stats['errors'] += 1
            log_connection_event("Error WebSocket", str(error))
            
            logger.error(f"Error de WebSocket recibido: {error}")
            logger.error(f"Tipo de error: {type(error)}")
            
            # Safely extract error details
            error_str = str(error).lower()
            
            # Handle different types of errors
            if "authentication" in error_str:
                logger.error("Error de autenticación - verificar credenciales")
            elif "connection" in error_str:
                logger.error("Error de conexión - verificar conectividad de red")
            elif isinstance(error, dict) and 'description' in error:
                desc = str(error.get('description', '')).lower()
                if "product" in desc:
                    logger.error(f"Error de producto - {error['description']}")
                else:
                    logger.error(f"Descripción del error: {error['description']}")
            else:
                logger.error(f"Error de WebSocket (raw): {error}")
            
            # IMPORTANT: Don't raise exceptions - just log and continue
            logger.info("Error registrado, continúo escuchando datos de mercado...")
            
        except Exception as e:
            # Catch any errors in error handler to prevent websocket from dying
            logger.error(f"Excepción en websocket_error_handler: {e}")
            logger.info("Continuando a pesar de la excepción en el manejador de errores...")
    
    def websocket_exception_handler(self, exception):
        """Manejar excepciones del WebSocket."""
        try:
            self.connection_stats['errors'] += 1
            log_connection_event("Excepción WebSocket", str(exception))
            
            logger.error(f"Excepción de WebSocket: {exception}")
            logger.error(f"Tipo de excepción: {type(exception)}")
            
            # Log exception details
            if hasattr(exception, '__traceback__'):
                import traceback
                logger.debug(f"Traza de la excepción: {traceback.format_exc()}")
            
            # IMPORTANT: Don't raise exceptions - just log and continue
            logger.info("Excepción registrada, continúo escuchando datos de mercado...")
            
        except Exception as e:
            # Catch any errors in exception handler to prevent websocket from dying
            logger.error(f"Excepción en websocket_exception_handler: {e}")
            logger.info("Continuando a pesar del error en el manejador de excepciones...")
    
    def on_error(self, online, error):
        """Manejar errores generales."""
        self.connection_stats['errors'] += 1
        log_connection_event("Error general", f"Online: {online}, Error: {error}")
        
        logger.error(f"Error general - Online: {online}, Error: {error}")
    
    def get_connection_stats(self) -> Dict[str, Any]:
        """Obtener estadísticas de conexión."""
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
        self._summary_logger.reset_all()
    
    def show_summary(self, force: bool = False):
        """
        Mostrar resumen de estadísticas de WebSocket.
        
        Args:
            force: Si True, muestra resumen sin importar intervalo
        """
        # Update summary stats
        self._summary_logger.set_stat('messages_received', self.connection_stats['messages_received'])
        self._summary_logger.set_stat('messages_processed', self.connection_stats['messages_processed'])
        self._summary_logger.set_stat('errors', self.connection_stats['errors'])
        
        if self.connection_stats['connection_start']:
            uptime = (datetime.now() - self.connection_stats['connection_start']).total_seconds()
            from ..utils.progress_logger import format_duration
            self._summary_logger.set_stat('uptime', format_duration(uptime))
        
        # Show summary
        self._summary_logger.show_summary("WebSocket Stats", force=force)
    
    def finish_progress(self):
        """Finalizar progreso y mover a nueva línea."""
        self._progress_logger.finish()