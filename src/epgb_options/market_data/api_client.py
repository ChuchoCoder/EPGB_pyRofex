"""
Cliente API de pyRofex

Este módulo maneja la conexión y configuración de la API de pyRofex.
"""

from typing import List, Set, Tuple

import pyRofex

from ..config.pyrofex_config import (ACCOUNT, API_URL, ENVIRONMENT, PASSWORD,
                                     USER, WS_URL)
from ..utils.logging import get_logger
from .instrument_cache import InstrumentCache

logger = get_logger(__name__)


class pyRofexClient:
    """Wrapper del cliente API de pyRofex."""
    
    def __init__(self):
        """Inicializar el cliente de pyRofex."""
        self.is_initialized = False
        self.is_authenticated = False
        self.instrument_cache = InstrumentCache(ttl_minutes=30)
        self._valid_instruments: Set[str] = set()
        
    def initialize(self):
        """Inicializar la conexión de pyRofex."""
        try:
            # Configurar parámetros de entorno
            pyRofex._set_environment_parameter('url', API_URL, getattr(pyRofex.Environment, ENVIRONMENT))
            pyRofex._set_environment_parameter('ws', WS_URL, getattr(pyRofex.Environment, ENVIRONMENT))
            
            # Inicializar
            pyRofex.initialize(environment=getattr(pyRofex.Environment, ENVIRONMENT),
                             user=USER, 
                             password=PASSWORD,
                             account=ACCOUNT)
            
            self.is_initialized = True
            logger.info(f"pyRofex inicializado con entorno: {ENVIRONMENT}")
            return True
            
        except Exception as e:
            error_msg = str(e)
            
            # Verificar si es un error de autenticación
            if "Authentication fails" in error_msg or "Incorrect User or Password" in error_msg:
                print("\n" + "="*70)
                print("\033[91m❌ FALLO DE AUTENTICACIÓN\033[0m")
                print("="*70)
                print("\033[91m🔐 PyRofex rechazó tus credenciales\033[0m")
                print(f"\nDetalles del error: {error_msg}")
                print("\n📋 Qué pasó:")
                print("   • La API de PyRofex rechazó la combinación de usuario/contraseña")
                print("   • Las credenciales de tu cuenta son incorrectas o están vencidas")
                print("\n🔧 Cómo arreglarlo:")
                print("   1. Verificá tus credenciales en: https://www.cocos.xoms.com.ar/")
                print("   2. Actualizá tus credenciales en UNO de estos lugares:")
                print("      → Archivo .env (recomendado):")
                print("         PYROFEX_USER=tu_usuario")
                print("         PYROFEX_PASSWORD=tu_contraseña")
                print("         PYROFEX_ACCOUNT=tu_cuenta")
                print("      → O en src/epgb_options/config/pyrofex_config.py")
                print("\n Consejo de seguridad: ¡Nunca subas credenciales a git!")
                print("="*70 + "\n")
                
                logger.error(f"🔐 Fallo de autenticación: {error_msg}")
            else:
                logger.error(f"Fallo al inicializar pyRofex: {e}")
            
            return False
    
    def fetch_available_instruments(self, force_refresh: bool = False) -> Set[str]:
        """
        Obtener instrumentos disponibles desde la API de pyRofex.
        Usa caché si está disponible y no expiró.
        
        Args:
            force_refresh: Forzar actualización desde API incluso si el caché es válido
            
        Returns:
            Set de símbolos de instrumentos válidos
        """
        try:
            # Intentar primero con caché a menos que se fuerce actualización
            if not force_refresh:
                cached_symbols = self.instrument_cache.get_instrument_symbols()
                if cached_symbols:
                    self._valid_instruments = cached_symbols
                    logger.info(f"Cargados {len(cached_symbols)} instrumentos desde caché")
                    return cached_symbols
            
            # Obtener desde API
            logger.info("Obteniendo instrumentos disponibles desde la API de pyRofex...")
            instrumentsResponse = pyRofex.get_detailed_instruments()
            
            if not instrumentsResponse:
                logger.warning("No se devolvieron instrumentos desde la API")
                return set()
            
            instruments = instrumentsResponse['instruments']
            
            if not instruments:
                logger.warning("No se encontraron instrumentos en la respuesta de la API")
                return set()

            # Registrar estructura de respuesta para depuración
            logger.debug(f"La API devolvió {len(instruments)} instrumentos, tipo: {type(instruments)}")
            if instruments and len(instruments) > 0:
                logger.debug(f"Tipo del primer instrumento: {type(instruments[0])}, muestra: {instruments[0] if isinstance(instruments[0], str) else str(instruments[0])[:100]}")
            
            # Guardar en caché
            self.instrument_cache.save_instruments(
                instruments,
                metadata={
                    'environment': ENVIRONMENT,
                    'fetched_by': 'pyRofexClient'
                }
            )
            
            # Extraer símbolos - manejar tanto formatos dict como string
            symbols = set()
            for instrument in instruments:
                if isinstance(instrument, str):
                    # Ya es un string de símbolo
                    symbols.add(instrument)
                elif isinstance(instrument, dict):
                    # Extraer símbolo del dict
                    symbol = instrument.get('symbol') or instrument.get('instrumentId', {}).get('symbol')
                    if symbol:
                        symbols.add(symbol)
                else:
                    logger.warning(f"Tipo de instrumento inesperado: {type(instrument)}")
            
            self._valid_instruments = symbols
            logger.info(f"Obtenidos {len(symbols)} instrumentos desde la API")
            return symbols
            
        except Exception as e:
            logger.error(f"Error al obtener instrumentos: {e}")
            # Devolver símbolos en caché como fallback
            cached_symbols = self.instrument_cache.get_instrument_symbols()
            if cached_symbols:
                logger.warning(f"Usando instrumentos en caché como fallback ({len(cached_symbols)} símbolos)")
                self._valid_instruments = cached_symbols
                return cached_symbols
            return set()
    
    def validate_symbols(self, symbols: List[str]) -> Tuple[List[str], List[str]]:
        """
        Validar símbolos contra instrumentos disponibles.
        
        Args:
            symbols: Lista de símbolos a validar
            
        Returns:
            Tupla de (símbolos_válidos, símbolos_inválidos)
        """
        if not self._valid_instruments:
            logger.warning("No hay instrumentos cargados, obteniendo ahora...")
            self.fetch_available_instruments()
        
        if not self._valid_instruments:
            logger.error("No se pueden validar símbolos - no hay instrumentos disponibles")
            return symbols, []  # Permitir todos los símbolos si no podemos validar
        
        valid = []
        invalid = []
        
        for symbol in symbols:
            if symbol in self._valid_instruments:
                valid.append(symbol)
            else:
                invalid.append(symbol)
        
        if invalid:
            logger.warning(f"Se encontraron {len(invalid)} símbolos inválidos: {invalid[:5]}{'...' if len(invalid) > 5 else ''}")
        
        logger.info(f"Validación de símbolos: {len(valid)} válidos, {len(invalid)} inválidos de {len(symbols)} totales")
        return valid, invalid
    
    def get_market_data(self, symbols, entries=None):
        """Obtener datos de mercado para símbolos."""
        if not self.is_initialized:
            raise RuntimeError("Cliente no inicializado. Llamá a initialize() primero.")
            
        if entries is None:
            # Solicitar todas las entradas de datos de mercado disponibles necesarias para las columnas de Excel
            entries = [
                pyRofex.MarketDataEntry.BIDS,               # Mejor compra (BI)
                pyRofex.MarketDataEntry.OFFERS,             # Mejor venta (OF)
                pyRofex.MarketDataEntry.LAST,               # Última operación (LA)
                pyRofex.MarketDataEntry.OPENING_PRICE,      # Precio de apertura (OP)
                pyRofex.MarketDataEntry.CLOSING_PRICE,      # Cierre anterior (CL)
                pyRofex.MarketDataEntry.HIGH_PRICE,         # Precio máximo (HI)
                pyRofex.MarketDataEntry.LOW_PRICE,          # Precio mínimo (LO)
                pyRofex.MarketDataEntry.TRADE_EFFECTIVE_VOLUME,  # Monto operado (EV)
                pyRofex.MarketDataEntry.NOMINAL_VOLUME,     # Volume (NV)
                pyRofex.MarketDataEntry.TRADE_COUNT,        # Operations/number of trades (TC)
            ]
            
        try:
            return pyRofex.get_market_data(symbols, entries)
        except Exception as e:
            logger.error(f"Failed to get market data: {e}")
            raise
    
    def subscribe_market_data(self, symbols):
        """
        Suscribirse a datos de mercado en tiempo real.
        
        IMPORTANTE: Se espera que los símbolos ya hayan sido validados previamente
        en _validate_and_filter_symbols() para evitar validación redundante.
        
        Args:
            symbols: Lista de símbolos pre-validados a los que suscribirse
            
        Returns:
            bool: True si la suscripción fue exitosa, False en caso contrario
        """
        if not self.is_initialized:
            raise RuntimeError("Cliente no inicializado. Llamá a initialize() primero.")
        
        logger.debug(f"Suscribiendo a {len(symbols)} símbolos pre-validados")
        
        # Definir entradas de datos de mercado necesarias para las columnas de Excel
        entries = [
            pyRofex.MarketDataEntry.BIDS,               # Mejor compra (BI)
            pyRofex.MarketDataEntry.OFFERS,             # Mejor venta (OF)
            pyRofex.MarketDataEntry.LAST,               # Última operación (LA)
            pyRofex.MarketDataEntry.OPENING_PRICE,      # Precio de apertura (OP)
            pyRofex.MarketDataEntry.CLOSING_PRICE,      # Cierre anterior (CL)
            pyRofex.MarketDataEntry.HIGH_PRICE,         # Precio máximo (HI)
            pyRofex.MarketDataEntry.LOW_PRICE,          # Precio mínimo (LO)
            pyRofex.MarketDataEntry.TRADE_EFFECTIVE_VOLUME,  # Monto operado (EV)
            pyRofex.MarketDataEntry.NOMINAL_VOLUME,     # Volumen (NV)
            pyRofex.MarketDataEntry.TRADE_COUNT,        # Operaciones/cantidad de operaciones (TC)
        ]
            
        try:
            pyRofex.market_data_subscription(tickers=symbols, entries=entries)
            logger.info(f"Suscripto a datos de mercado para {len(symbols)} símbolos")
            return True
        except Exception as e:
            logger.error(f"Fallo al suscribirse a datos de mercado: {e}")
            return False
    
    def set_market_data_handler(self, handler):
        """Registrar (agregar) el manejador de mensajes de datos de mercado (API pyRofex 0.5.x)."""
        if not callable(handler):
            raise ValueError("El manejador debe ser invocable")
        # pyRofex 0.5.0 provee add_websocket_market_data_handler
        if hasattr(pyRofex, 'add_websocket_market_data_handler'):
            pyRofex.add_websocket_market_data_handler(handler)
            logger.info("Manejador de datos de mercado registrado")
        else:
            raise AttributeError("El módulo pyRofex no tiene add_websocket_market_data_handler")
    
    def set_error_handler(self, handler):
        """Registrar (agregar) el manejador de errores de websocket.""" 
        if not callable(handler):
            raise ValueError("El manejador debe ser invocable")
        if hasattr(pyRofex, 'add_websocket_error_handler'):
            pyRofex.add_websocket_error_handler(handler)
            logger.info("Manejador de errores registrado")
        else:
            logger.warning("pyRofex no tiene add_websocket_error_handler; manejador no configurado")
    
    def set_exception_handler(self, handler):
        """Configurar el manejador de excepciones de websocket (el nombre difiere en 0.5.x)."""
        if not callable(handler):
            raise ValueError("El manejador debe ser invocable")
        if hasattr(pyRofex, 'set_websocket_exception_handler'):
            pyRofex.set_websocket_exception_handler(handler)
            logger.info("Manejador de excepciones configurado")
        else:
            logger.warning("pyRofex no tiene set_websocket_exception_handler; manejador de excepciones no configurado")
    
    def subscribe_order_reports(self):
        """
        Subscribe to order reports via WebSocket.
        Provides real-time updates for order status changes and executions.
        """
        if not self.is_initialized:
            raise RuntimeError("Cliente no inicializado. Llamá a initialize() primero.")
        
        try:
            pyRofex.order_report_subscription()
            logger.info("Suscripto a reportes de órdenes")
            return True
        except Exception as e:
            logger.error(f"Fallo al suscribirse a reportes de órdenes: {e}")
            return False
    
    def set_order_report_handler(self, handler):
        """
        Register handler for order report messages.
        
        Args:
            handler: Callable that receives order report messages
        """
        if not callable(handler):
            raise ValueError("El manejador debe ser invocable")
        
        if hasattr(pyRofex, 'add_websocket_order_report_handler'):
            pyRofex.add_websocket_order_report_handler(handler)
            logger.info("Manejador de reportes de órdenes registrado")
        else:
            logger.warning("pyRofex no tiene add_websocket_order_report_handler; manejador no configurado")
    
    def get_filled_orders(self):
        """
        Fetch all filled/partially filled orders via REST API.
        
        Calls GET /rest/order/filleds endpoint.
        
        Returns:
            dict: Response containing filled orders, or None on error
                {
                    'status': 'OK',
                    'orders': [
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
                            'transactTime': str,
                            'avgPx': float,
                            'lastPx': float,
                            'lastQty': int,
                            'cumQty': int,
                            'leavesQty': int,
                            'status': str,
                            'text': str
                        },
                        ...
                    ]
                }
        """
        if not self.is_initialized:
            raise RuntimeError("Cliente no inicializado. Llamá a initialize() primero.")
        
        try:
            # pyRofex provides get_order_status for individual orders
            # For filled orders, we need to use the REST endpoint directly
            # The pyRofex library doesn't have a direct method for /rest/order/filleds
            # So we'll use get_all_orders which should return all orders
            
            logger.debug(f"Fetching filled orders for account {ACCOUNT}...")
            
            # Try using pyRofex's get_all_orders if available
            if hasattr(pyRofex, 'get_all_orders'):
                response = pyRofex.get_all_orders(account_id=ACCOUNT)
            else:
                # pyRofex doesn't have get_all_orders, use custom HTTP request
                logger.debug("Using custom HTTP request for filled orders endpoint")
                import requests

                # Access the auth token from pyRofex's environment config
                try:
                    from pyRofex.components.enums import Environment
                    from pyRofex.components.globals import environment_config
                    
                    env = getattr(Environment, ENVIRONMENT)
                    auth_token = environment_config.get(env, {}).get('token')
                    
                    if not auth_token:
                        logger.error("Cannot fetch filled orders: No auth token in pyRofex environment config")
                        return None
                    
                    # Build request
                    headers = {
                        'X-Auth-Token': auth_token
                    }
                    url = f"{API_URL}rest/order/filleds"
                    params = {'accountId': ACCOUNT}
                    
                    logger.debug(f"Calling {url} with accountId={ACCOUNT}")
                    response = requests.get(url, headers=headers, params=params, timeout=10)
                    response.raise_for_status()
                    response = response.json()
                    
                except ImportError as ie:
                    logger.error(f"Cannot import pyRofex internals: {ie}")
                    return None
                except requests.exceptions.RequestException as re:
                    logger.error(f"HTTP request failed: {re}")
                    return None
            
            # Validate response
            if not response or response.get('status') != 'OK':
                logger.debug(f"Filled orders request failed or returned non-OK status: {response}")
                return None
            
            orders = response.get('orders', [])
            logger.debug(f"Fetched {len(orders)} filled orders from API")
            
            return response
            
        except Exception as e:
            logger.error(f"Error fetching filled orders: {e}", exc_info=True)
            return None
    
    def close_connection(self):
        """Cerrar la conexión de pyRofex."""
        if self.is_initialized:
            try:
                pyRofex.close_websocket_connection()
                logger.info("Conexión de pyRofex cerrada")
            except Exception as e:
                logger.warning(f"Error al cerrar conexión: {e}")
        
        self.is_initialized = False
        self.is_authenticated = False