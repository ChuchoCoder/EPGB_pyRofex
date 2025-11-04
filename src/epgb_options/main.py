"""
Punto de entrada principal de la aplicación EPGB Options.

Este módulo provee la lógica principal de la aplicación y coordina
todos los diferentes componentes.
"""

import time
from datetime import datetime
from typing import Any, Dict

import pandas as pd

from .config import (EXCEL_FILE, EXCEL_PATH, EXCEL_SHEET_PRICES,
                     EXCEL_SHEET_TICKERS, EXCEL_UPDATE_INTERVAL,
                     TRADES_REALTIME_ENABLED, TRADES_SYNC_ENABLED,
                     TRADES_SYNC_INTERVAL_SECONDS, validate_excel_config,
                     validate_pyRofex_config)
from .excel import SheetOperations, SymbolLoader, WorkbookManager
from .market_data import DataProcessor, WebSocketHandler, pyRofexClient
from .trades import ExecutionFetcher, TradesProcessor, TradesUpserter
from .utils import get_logger, log_connection_event, setup_logging
from .utils.progress_logger import ProgressLogger, SummaryLogger, format_number

logger = get_logger(__name__)


class EPGBOptionsApp:
    """Clase principal de la aplicación EPGB Options."""
    
    def __init__(self):
        """Inicializar la aplicación."""
        self.api_client = None
        self.websocket_handler = None
        self.data_processor = None
        self.workbook_manager = None
        self.symbol_loader = None
        self.sheet_operations = None
        
        # Trades components
        self.execution_fetcher = None
        self.trades_processor = None
        self.trades_upserter = None
        self.last_trades_sync_time = None
        
        # Data storage
        self.options_df = pd.DataFrame()
        self.everything_df = pd.DataFrame()
        self.cauciones_df = pd.DataFrame()
        self.futuros_df = pd.DataFrame()
        
        # Application state
        self.is_running = False
        self.last_update_time = None
        self.last_excel_update_time = None  # When Excel was last updated
        self.last_market_data_time = None   # When market data was last received
        
        # Excel update statistics
        self.excel_update_stats = {
            'total_cycles': 0,
            'updates_performed': 0,
            'updates_skipped': 0
        }
        
        # Orders/trades statistics
        self.orders_stats = {
            'total_filled': 0,
            'last_sync_count': 0,
            'last_sync_processed': 0,     # Executions processed in last sync
            'last_sync_inserted': 0,      # New trades inserted
            'last_sync_updated': 0        # Existing trades updated
        }
        
        # Unified single-line status display
        self._status_logger = ProgressLogger(throttle_seconds=0.5)
        
        # Summary logger for periodic stats (every 60s, less frequent)
        self._summary_logger = SummaryLogger(logger, interval_seconds=60.0)
    
    def initialize(self) -> bool:
        """
        Inicializar todos los componentes de la aplicación.
        
        Returns:
            bool: True si la inicialización fue exitosa, False en caso contrario
        """
        try:
            logger.info("Inicializando aplicación EPGB Options")
            
            # Configurar logging
            setup_logging()
            
            # Validar configuraciones
            if not self._validate_configurations():
                return False
            
            # Inicializar componentes de datos de mercado (poblar cache de instrumentos)
            if not self._initialize_market_data_components():
                return False
            
            # Inicializar componentes de Excel
            if not self._initialize_excel_components():
                return False
            
            # Cargar símbolos desde Excel
            if not self._load_symbols():
                return False
            
            # Validar y filtrar símbolos contra el cache de instrumentos
            if not self._validate_and_filter_symbols():
                return False
            
            # Configurar referencias de datos ahora que los DataFrames están cargados y validados
            self.websocket_handler.set_data_references(self.options_df, self.everything_df, self.cauciones_df)
            
            # Configurar cache de instrumentos en sheet operations para detección de opciones
            self.sheet_operations.set_instrument_cache(self.api_client.instrument_cache)
            
            # Inicializar componentes de Trades si está habilitado
            logger.debug(f"TRADES_SYNC_ENABLED = {TRADES_SYNC_ENABLED}")
            if TRADES_SYNC_ENABLED:
                logger.info("Trades sync está habilitado, inicializando componentes...")
                try:
                    if not self._initialize_trades_components():
                        logger.warning("No se pudieron inicializar componentes de Trades, continuando sin sincronización de trades")
                except Exception as e:
                    logger.error(f"❌ Error al inicializar Trades: {e}", exc_info=True)
            else:
                logger.info("Trades sync deshabilitado (TRADES_SYNC_ENABLED=False)")
            
            logger.info("✅ Inicialización de la aplicación completada exitosamente")
            return True
            
        except Exception as e:
            logger.error(f"Fallo al inicializar la aplicación: {e}")
            return False
    
    def _validate_configurations(self) -> bool:
        """Validar todos los archivos de configuración."""
        logger.info("Validando configuraciones...")
        
        # Validar configuración de Excel
        excel_errors = validate_excel_config()
        if excel_errors:
            logger.error("Errores de configuración de Excel:")
            for error in excel_errors:
                logger.error(f"  - {error}")
            return False
        
        # Validar configuración de pyRofex
        pyrofex_errors = validate_pyRofex_config()
        if pyrofex_errors:
            logger.error("Errores de configuración de pyRofex:")
            for error in pyrofex_errors:
                logger.error(f"  - {error}")
            
            # Verificar valores de placeholder específicamente
            if any("placeholder" in error.lower() for error in pyrofex_errors):
                logger.error("🛑 DETENIENDO EJECUCIÓN - Se requiere configuración manual de credenciales")
                logger.error("Por favor configurá tus credenciales en:")
                logger.error("   - pyRofex_config.py (o)")
                logger.error("   - Variables de entorno: PYROFEX_USER, PYROFEX_PASSWORD, PYROFEX_ACCOUNT")
                return False
        
        logger.info("✅ Validación de configuración exitosa")
        return True
    
    def _initialize_excel_components(self) -> bool:
        """Inicializar componentes relacionados a Excel."""
        try:
            logger.info("Inicializando componentes de Excel...")
            
            # Inicializar el administrador de libro
            self.workbook_manager = WorkbookManager(EXCEL_FILE, EXCEL_PATH)
            if not self.workbook_manager.connect():
                return False
            
            # Obtener hoja de tickers
            tickers_sheet = self.workbook_manager.get_sheet(EXCEL_SHEET_TICKERS)
            if not tickers_sheet:
                logger.error(f"No se pudo acceder a la hoja {EXCEL_SHEET_TICKERS}")
                return False
            
            # Inicializar cargador de símbolos
            self.symbol_loader = SymbolLoader(tickers_sheet)
            
            # Inicializar operaciones de hojas
            self.sheet_operations = SheetOperations(self.workbook_manager.workbook)
            
            logger.info("✅ Componentes de Excel inicializados")
            return True
            
        except Exception as e:
            logger.error(f"Error al inicializar componentes de Excel: {e}")
            return False
    
    def _load_symbols(self) -> bool:
        """Cargar símbolos desde las hojas de Excel."""
        try:
            logger.info("Cargando símbolos desde Excel...")
            
            # Cargar todos los tipos de símbolos
            all_symbols = self.symbol_loader.get_all_symbols()
            
            # Almacenar opciones por separado
            self.options_df = all_symbols.get('options', pd.DataFrame())
            
            # Almacenar cauciones por separado (sólo van a la tabla del lado derecho)
            self.cauciones_df = all_symbols.get('cauciones', pd.DataFrame())
            
            # Almacenar futuros por separado para referencia
            self.futuros_df = all_symbols.get('futuros', pd.DataFrame())
            logger.info(f"Cargados {len(self.futuros_df)} símbolos de futuros desde Excel")
            
            # Combinar otros valores (incluir futuros, excluir cauciones de la tabla principal)
            securities_to_combine = ['acciones', 'bonos', 'cedears', 'letras', 'ons', 'panel_general', 'futuros']
            securities_dfs = [all_symbols.get(key, pd.DataFrame()) for key in securities_to_combine]
            valid_securities = [df for df in securities_dfs if not df.empty]
            
            if valid_securities:
                self.everything_df = pd.concat(valid_securities, ignore_index=False)
            else:
                self.everything_df = pd.DataFrame()
            
            # Registrar resumen
            symbol_counts = self.symbol_loader.get_symbol_count_by_type()
            logger.info("Resumen de carga de símbolos:")
            for symbol_type, count in symbol_counts.items():
                logger.info(f"  - {symbol_type}: {count} símbolos")
            
            total_symbols = len(self.options_df) + len(self.everything_df)
            logger.info(f"✅ Total de símbolos cargados: {total_symbols}")
            
            return total_symbols > 0
            
        except Exception as e:
            logger.error(f"Error al cargar símbolos: {e}")
            return False
    
    def _validate_and_filter_symbols(self) -> bool:
        """
        Validar y filtrar símbolos contra el cache de instrumentos disponibles.
        
        Remueve símbolos del Excel que no existen en el mercado según pyRofex.
        
        Returns:
            bool: True si quedan símbolos válidos después del filtrado, False en caso contrario
        """
        try:
            logger.info("Validando símbolos contra instrumentos disponibles en pyRofex...")
            
            total_invalid = 0
            
            # Validar opciones
            if not self.options_df.empty:
                original_count = len(self.options_df)
                valid_options, invalid_options = self.api_client.validate_symbols(
                    list(self.options_df.index)
                )
                
                if invalid_options:
                    logger.warning(f"{len(invalid_options)} opciones inválidas encontradas en Excel:")
                    for symbol in invalid_options[:10]:  # Mostrar primeras 10
                        logger.warning(f"    - {symbol}")
                    if len(invalid_options) > 10:
                        logger.warning(f"    ... y {len(invalid_options) - 10} más")
                    
                    # Filtrar símbolos inválidos
                    self.options_df = self.options_df.loc[valid_options]
                    total_invalid += len(invalid_options)
                    logger.info(f"Opciones: {len(valid_options)}/{original_count} válidas")
            
            # Validar valores
            if not self.everything_df.empty:
                original_count = len(self.everything_df)
                valid_securities, invalid_securities = self.api_client.validate_symbols(
                    list(self.everything_df.index)
                )
                
                if invalid_securities:
                    logger.warning(f"{len(invalid_securities)} valores inválidos encontrados en Excel:")
                    for symbol in invalid_securities[:10]:
                        logger.warning(f"    - {symbol}")
                    if len(invalid_securities) > 10:
                        logger.warning(f"    ... y {len(invalid_securities) - 10} más")
                    
                    # Filtrar símbolos inválidos
                    self.everything_df = self.everything_df.loc[valid_securities]
                    total_invalid += len(invalid_securities)
                    
                    # Also filter from futuros_df if symbols were removed
                    if not self.futuros_df.empty:
                        futures_to_remove = [s for s in invalid_securities if s in self.futuros_df.index]
                        if futures_to_remove:
                            self.futuros_df = self.futuros_df.drop(futures_to_remove, errors='ignore')
                            logger.info(f"  - {len(futures_to_remove)} futuros inválidos removidos")
                    
                    logger.info(f"Valores: {len(valid_securities)}/{original_count} válidos")
                else:
                    logger.info(f"Valores: {original_count}/{original_count} válidos")
                
                # Log futures validation separately for clarity
                if not self.futuros_df.empty:
                    futures_count = len(self.futuros_df)
                    futures_symbols = list(self.futuros_df.index)
                    valid_futures = [s for s in futures_symbols if s in valid_securities]
                    logger.info(f"  - Futuros: {len(valid_futures)}/{futures_count} válidos")
            
            # Validar cauciones
            if not self.cauciones_df.empty:
                original_count = len(self.cauciones_df)
                valid_cauciones, invalid_cauciones = self.api_client.validate_symbols(
                    list(self.cauciones_df.index)
                )
                
                if invalid_cauciones:
                    logger.warning(f"{len(invalid_cauciones)} cauciones inválidas encontradas en Excel:")
                    for symbol in invalid_cauciones[:10]:
                        logger.warning(f"    - {symbol}")
                    if len(invalid_cauciones) > 10:
                        logger.warning(f"    ... y {len(invalid_cauciones) - 10} más")
                    
                    # Filtrar símbolos inválidos
                    self.cauciones_df = self.cauciones_df.loc[valid_cauciones]
                    total_invalid += len(invalid_cauciones)
                    logger.info(f"Cauciones: {len(valid_cauciones)}/{original_count} válidas")
            
            # Resumen final
            total_valid = len(self.options_df) + len(self.everything_df) + len(self.cauciones_df)
            
            if total_invalid > 0:
                logger.warning(f"Total: {total_invalid} símbolos inválidos removidos del Excel")
            
            logger.info(f"✅ {total_valid} símbolos válidos listos para suscripción")
            
            if total_valid == 0:
                logger.error("❌ No hay símbolos válidos después del filtrado")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error al validar y filtrar símbolos: {e}")
            return False
    
    def _initialize_market_data_components(self) -> bool:
        """Inicializar componentes de datos de mercado."""
        try:
            logger.info("Inicializando componentes de datos de mercado...")
            
            # Inicializar cliente API
            self.api_client = pyRofexClient()
            if not self.api_client.initialize():
                print("\n" + "="*70)
                print("\033[91m🛑 FALLO DE INICIALIZACIÓN - La aplicación no puede continuar\033[0m")
                print("="*70)
                print("\033[91mEl cliente de la API PyRofex falló al inicializar\033[0m")
                print("\n📋 Qué significa esto:")
                print("   • La aplicación no puede conectarse a la API de datos de mercado de PyRofex")
                print("   • Causa más probable: Fallo de autenticación (credenciales incorrectas)")
                print("   • Revisá los mensajes de error de arriba para detalles específicos")
                print("\n🔧 Próximos pasos:")
                print("   1. Revisá los detalles del error de autenticación arriba")
                print("   2. Corregí tus credenciales (mirá las instrucciones arriba)")
                print("   3. Volvé a ejecutar la aplicación")
                print("\n💡 ¿Necesitás ayuda? Consultá el archivo README.md para instrucciones de configuración")
                print("="*70 + "\n")
                
                logger.error("🛑 Fallo al inicializar el cliente de la API de pyRofex - deteniendo aplicación")
                return False
            
            # CRITICAL: Pre-cargar instrumentos ANTES de inicializar WebSocketHandler
            # Esto asegura que el caché de instrumentos esté poblado antes de cualquier
            # procesamiento de mensajes de WebSocket
            logger.info("Pre-cargando instrumentos disponibles desde pyRofex...")
            available_instruments = self.api_client.fetch_available_instruments()
            logger.info(f"✅ Pre-cargados {len(available_instruments)} instrumentos al caché")
            
            # Verificar que el caché está poblado correctamente
            cache_stats = self.api_client.instrument_cache.get_cache_stats()
            logger.info(f"📊 Caché de instrumentos: {cache_stats['total_instruments']} instrumentos, {cache_stats['total_options']} opciones")
            
            if cache_stats['total_options'] == 0:
                logger.warning("No se encontraron opciones en el caché de instrumentos")
            
            # Inicializar manejador de WebSocket con caché de instrumentos compartido (ya poblado)
            # Nota: set_data_references será llamado después de cargar símbolos desde Excel
            self.websocket_handler = WebSocketHandler(instrument_cache=self.api_client.instrument_cache)
            self.websocket_handler.set_update_callback(self._on_data_update)
            
            # Inicializar procesador de datos
            self.data_processor = DataProcessor()
            
            # Configurar manejadores de WebSocket
            self.api_client.set_market_data_handler(self.websocket_handler.market_data_handler)
            self.api_client.set_error_handler(self.websocket_handler.websocket_error_handler)
            self.api_client.set_exception_handler(self.websocket_handler.websocket_exception_handler)
            
            logger.info("✅ Componentes de datos de mercado inicializados")
            return True
            
        except Exception as e:
            logger.error(f"Error al inicializar componentes de datos de mercado: {e}")
            return False
    
    def _initialize_trades_components(self) -> bool:
        """
        Inicializar componentes de trades para sincronización automática de ejecuciones.
        
        Returns:
            bool: True si la inicialización fue exitosa, False en caso contrario
        """
        try:
            logger.info("Inicializando componentes de Trades...")
            
            # Initialize trades processor
            self.trades_processor = TradesProcessor()
            
            # Initialize trades upserter with workbook and status logger
            if not self.workbook_manager or not self.workbook_manager.workbook:
                logger.error("Workbook manager no disponible para trades upserter")
                return False
            
            self.trades_upserter = TradesUpserter(self.workbook_manager.workbook, self._status_logger)
            
            # Initialize execution fetcher
            self.execution_fetcher = ExecutionFetcher(self.api_client)
            
            # STARTUP SYNC: Fetch all existing filled orders and populate Trades sheet
            logger.info("🔄 Sincronizando órdenes ejecutadas existentes desde la API...")
            self._sync_filled_orders()
            
            # Set up real-time updates if enabled
            if TRADES_REALTIME_ENABLED:
                logger.info("⚡ Real-time trades updates ENABLED via WebSocket")
                
                # Define execution callback for real-time updates
                def on_execution(execution):
                    """Callback for new executions from WebSocket."""
                    try:
                        # Process execution
                        df = self.trades_processor.process_executions([execution])
                        if not df.empty:
                            # Upsert to Excel
                            stats = self.trades_upserter.upsert_executions(df)
                            logger.info(f"⚡ Real-time execution upserted: {stats}")
                    except Exception as e:
                        logger.error(f"Error processing execution callback: {e}", exc_info=True)
                
                # Subscribe to order reports with callback
                self.api_client.set_order_report_handler(
                    lambda msg: self.execution_fetcher._parse_order_report(msg) and on_execution(
                        self.execution_fetcher._parse_order_report(msg)
                    )
                )
                
                if not self.api_client.subscribe_order_reports():
                    logger.error("Failed to subscribe to order reports")
                    return False
            else:
                logger.info(f"⏱️  Real-time trades updates DISABLED - using periodic sync every {TRADES_SYNC_INTERVAL_SECONDS}s")
            
            # Initialize sync timer
            self.last_trades_sync_time = datetime.now()
            
            logger.info("✅ Componentes de Trades inicializados correctamente")
            return True
            
        except Exception as e:
            logger.error(f"Error al inicializar componentes de Trades: {e}", exc_info=True)
            return False
    
    def _sync_filled_orders(self):
        """
        Sync filled orders from broker API via REST.
        Called at startup and periodically if real-time is disabled.
        """
        try:
            filled_orders = self.execution_fetcher.fetch_filled_orders_at_startup()
            
            if filled_orders:
                order_count = len(filled_orders)
                logger.debug(f"Procesando {order_count} órdenes ejecutadas para upsert...")
                
                # Update stats - set to current count, not accumulate
                self.orders_stats['last_sync_count'] = order_count
                self.orders_stats['total_filled'] = order_count
                
                # Process executions
                df = self.trades_processor.process_executions(filled_orders)
                
                if not df.empty:
                    # Upsert to Excel
                    stats = self.trades_upserter.upsert_executions(df)
                    
                    # Capture stats for unified status line
                    self.orders_stats['last_sync_processed'] = len(df)
                    self.orders_stats['last_sync_inserted'] = stats.get('inserted', 0)
                    self.orders_stats['last_sync_updated'] = stats.get('updated', 0)
                    
                    logger.debug(f"Sincronización completa: {stats}")
                else:
                    logger.debug("No se pudieron procesar órdenes ejecutadas en DataFrame")
                    self.orders_stats['last_sync_processed'] = 0
                    self.orders_stats['last_sync_inserted'] = 0
                    self.orders_stats['last_sync_updated'] = 0
            else:
                self.orders_stats['last_sync_count'] = 0
                self.orders_stats['last_sync_processed'] = 0
                self.orders_stats['last_sync_inserted'] = 0
                self.orders_stats['last_sync_updated'] = 0
                logger.debug("No hay órdenes ejecutadas para sincronizar")
        except Exception as e:
            logger.error(f"Error en sincronización de órdenes: {e}", exc_info=True)
    
    def _check_and_sync_trades(self):
        """
        Check if it's time to sync trades and trigger sync if needed.
        Only used when real-time updates are disabled.
        """
        if not self.last_trades_sync_time or not self.execution_fetcher:
            return
        
        elapsed = (datetime.now() - self.last_trades_sync_time).total_seconds()
        
        if elapsed >= TRADES_SYNC_INTERVAL_SECONDS:
            # Sync quietly - status shown in unified line
            logger.debug(f"Periodic trades sync triggered ({elapsed:.0f}s elapsed)")
            self._sync_filled_orders()
            self.last_trades_sync_time = datetime.now()
    
    def _check_market_data_timeout(self):
        """
        Check if market data has been received recently.
        Timeout warnings are now shown in the unified status line (not as separate log entries).
        """
        if not self.websocket_handler:
            return
        
        stats = self.websocket_handler.get_connection_stats()
        last_message_time = stats.get('last_message_time')
        
        if last_message_time:
            
            # Warning if no data for 10+ seconds - but DON'T log it here
            # The unified status line in _update_unified_status() will show the timeout
            # This prevents creating new log lines
    
    def _on_data_update(self, symbol: str, message: Dict[str, Any]):
        """
        Callback para cuando los datos de mercado se actualizan.
        
        Args:
            symbol: Símbolo actualizado
            message: Mensaje de datos de mercado
        """
        current_time = datetime.now()
        self.last_update_time = current_time
        self.last_market_data_time = current_time  # Track when market data was received
        logger.debug(f"Callback de actualización de datos para {symbol}")
        
        # Podrías disparar actualizaciones de Excel acá o agruparlas
        # Por ahora, sólo registramos la actualización
    
    def _should_update_excel(self) -> bool:
        """
        Determine if Excel should be updated based on market data availability.
        
        Skip Excel updates if no new market data has been received since the last update.
        This optimization reduces unnecessary Excel writes during low-activity periods.
        
        Returns:
            bool: True if Excel should be updated, False to skip this cycle
        """
        # First run - always update to initialize Excel
        if self.last_excel_update_time is None:
            logger.info("📊 Primera actualización de Excel - inicializando")
            return True
        
        # No market data received yet - skip update
        if self.last_market_data_time is None:
            logger.debug("Sin datos de mercado recibidos aún - omitiendo actualización de Excel")
            return False
        
        # Check if we have new market data since last Excel update
        if self.last_market_data_time > self.last_excel_update_time:
            elapsed = (self.last_market_data_time - self.last_excel_update_time).total_seconds()
            logger.debug(f"Nuevos datos de mercado disponibles (hace {elapsed:.1f}s) - actualizando Excel")
            return True
        else:
            elapsed = (datetime.now() - self.last_excel_update_time).total_seconds()
            logger.debug(f"Sin nuevos datos de mercado (última actualización hace {elapsed:.1f}s) - omitiendo Excel")
            return False
    
    def start_market_data_subscription(self) -> bool:
        """
        Comenzar suscripción a datos de mercado.
        
        Nota: Los símbolos ya fueron validados y filtrados en _validate_and_filter_symbols(),
        por lo que todos los símbolos en los DataFrames son válidos.
        """
        try:
            logger.info("Iniciando suscripción a datos de mercado...")
            
            # Suscribirse a opciones (ya validadas)
            if not self.options_df.empty:
                options_symbols = list(self.options_df.index)
                if not self.api_client.subscribe_market_data(options_symbols):
                    logger.error("Fallo al suscribirse a datos de opciones")
                    return False
                logger.info(f"✅ Suscripto a {len(options_symbols)} opciones")
            
            # Suscribirse a otros valores (ya validados)
            if not self.everything_df.empty:
                securities_symbols = list(self.everything_df.index)
                if not self.api_client.subscribe_market_data(securities_symbols):
                    logger.error("Fallo al suscribirse a datos de valores")
                    return False
                logger.info(f"✅ Suscripto a {len(securities_symbols)} valores")
                
                # Log futures subscription separately for clarity
                if not self.futuros_df.empty:
                    futures_count = len(self.futuros_df)
                    logger.info(f"  - Incluye {futures_count} futuros")
            
            # Suscribirse a cauciones (ya validadas)
            if not self.cauciones_df.empty:
                cauciones_symbols = list(self.cauciones_df.index)
                if self.api_client.subscribe_market_data(cauciones_symbols):
                    logger.info(f"✅ Suscripto a {len(cauciones_symbols)} cauciones")
                else:
                    logger.warning("No se pudo suscribir a cauciones")
            
            log_connection_event("Suscripción a Datos de Mercado", "Iniciado exitosamente")
            return True
            
        except Exception as e:
            logger.error(f"Error al iniciar suscripción a datos de mercado: {e}")
            return False
    
    def update_excel_with_current_data(self) -> bool:
        """Actualizar Excel con los datos de mercado actuales."""
        try:
            logger.debug("Actualizando Excel con datos actuales...")
            
            # Actualizar hoja Prices con datos de valores (excluyendo cauciones)
            if not self.everything_df.empty:
                success = self.sheet_operations.update_market_data_to_prices_sheet(
                    self.everything_df, EXCEL_SHEET_PRICES, self.cauciones_df
                )
                if not success:
                    logger.warning("Fallo al actualizar hoja Prices")
            
            # Actualizar opciones en Prices sheet
            if not self.options_df.empty:
                # Opciones usan bidsize/asksize sin underscore, necesitamos renombrar para compatibilidad con Excel
                options_for_excel = self.options_df.copy()
                options_for_excel = options_for_excel.rename(columns={'bidsize': 'bid_size', 'asksize': 'ask_size'})
                
                success = self.sheet_operations.update_market_data_to_prices_sheet(
                    options_for_excel, EXCEL_SHEET_PRICES, cauciones_df=None
                )
                if not success:
                    logger.warning("Fallo al actualizar opciones en Prices")
            
            logger.debug("Actualización de Excel completada")
            return True
            
        except Exception as e:
            logger.error(f"Error al actualizar Excel: {e}")
            return False
    
    def _update_unified_status(self):
        """Actualizar línea única de estado con toda la información relevante."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        # WebSocket stats
        ws_stats = self.websocket_handler.get_connection_stats()
        msgs = ws_stats['messages_received']
        processed = ws_stats['messages_processed']
        errors = ws_stats['errors']
        
        # Excel stats
        cycle = self.excel_update_stats['total_cycles']
        excel_updates = self.excel_update_stats['updates_performed']
        
        # Orders stats (if trades sync is enabled)
        orders_str = ""
        if TRADES_SYNC_ENABLED:
            orders_count = self.orders_stats['total_filled']
            orders_str = f" | 📝 {orders_count} orders"
            
            # Add execution details if there were any in last sync
            last_processed = self.orders_stats.get('last_sync_processed', 0)
            if last_processed > 0:
                last_inserted = self.orders_stats.get('last_sync_inserted', 0)
                last_updated = self.orders_stats.get('last_sync_updated', 0)
                
                # Build compact execution stats string
                exec_parts = []
                if last_inserted > 0:
                    exec_parts.append(f"+{last_inserted} ins")
                if last_updated > 0:
                    exec_parts.append(f"~{last_updated} upd")
                
                if exec_parts:
                    exec_str = ", ".join(exec_parts)
                    orders_str += f" | ✅ {last_processed} exec ({exec_str})"
        
        # Market data timeout warning
        timeout_str = ""
        if ws_stats['last_message_time']:
            seconds_since_last = (datetime.now() - ws_stats['last_message_time']).total_seconds()
            if seconds_since_last > 10:
                timeout_str = f" | 🟡 Sin datos {int(seconds_since_last)}s"
        
        # Build unified status line
        status = (
            f"[{timestamp}] 📊 Ciclo {cycle} | "
            f"📡 WS: {processed}/{msgs} msgs ({errors} err) | "
            f"📈 Excel: {excel_updates} acts.{orders_str}{timeout_str}"
        )
        
        self._status_logger.update(status)
    
    def run(self):
        """Ejecutar el bucle principal de la aplicación."""
        try:
            logger.info("🚀 Iniciando aplicación de Datos de Mercado EPGB Options")
            
            if not self.initialize():
                print("\n" + "="*70)
                print("\033[91m💥 FALLO DE INICIO DE APLICACIÓN\033[0m")
                print("="*70)
                print("\033[91m❌ La aplicación no pudo inicializarse correctamente\033[0m")
                print("\n📋 Causas comunes:")
                print("   • Credenciales de PyRofex incorrectas (más común)")
                print("   • Archivo de Excel no encontrado o no se puede abrir")
                print("   • Archivos de configuración faltantes o inválidos")
                print("\n🔍 Revisá los mensajes de error de arriba para identificar el problema específico")
                print("\n🔧 Una vez que corrijas el problema, ejecutá la aplicación de nuevo:")
                print("   python -m epgb_options")
                print("   # o")
                print("   epgb-options")
                print("="*70 + "\n")
                
                logger.error("🛑 Fallo de inicialización - deteniendo aplicación")
                return
            
            if not self.start_market_data_subscription():
                logger.error("Fallo de suscripción a datos de mercado - deteniendo aplicación")
                return
            
            self.is_running = True
            logger.info("✅ Aplicación ejecutándose - streaming de datos de mercado iniciado")
            
            # Esperar a que los datos de mercado iniciales se poblen (dar tiempo al WebSocket para recibir primer lote)
            logger.info("Esperando que los datos de mercado iniciales se pueblen...")
            time.sleep(2)
            logger.info("✅ Iniciando bucle principal - todos los logs se mostrarán en UNA línea actualizable")
            
            # Bucle principal de la aplicación
            try:
                while self.is_running:
                    # Increment total cycles counter
                    self.excel_update_stats['total_cycles'] += 1
                    cycle_num = self.excel_update_stats['total_cycles']
                    
                    # Check for market data timeout (no data received for 10+ seconds)
                    self._check_market_data_timeout()
                    
                    # Check if Excel update is needed (optimization: skip if no new data)
                    if self._should_update_excel():
                        # Actualizar Excel con nuevos datos
                        self.update_excel_with_current_data()
                        
                        # Record the update time and increment counter
                        self.last_excel_update_time = datetime.now()
                        self.excel_update_stats['updates_performed'] += 1
                        
                        # Update summary logger
                        self._summary_logger.increment('excel_updates')
                    else:
                        # Skip this update - no new data
                        self.excel_update_stats['updates_skipped'] += 1
                        self._summary_logger.increment('excel_skipped')
                    
                    # Update unified status line (replaces all individual progress logs)
                    self._update_unified_status()
                    
                    # Periodic trades sync if real-time is disabled
                    if TRADES_SYNC_ENABLED and not TRADES_REALTIME_ENABLED:
                        self._check_and_sync_trades()
                    
                    # Show full summary only occasionally (every 60 cycles)
                    if cycle_num % 60 == 0:
                        ws_stats = self.websocket_handler.get_connection_stats()
                        performed = self.excel_update_stats['updates_performed']
                        skipped = self.excel_update_stats['updates_skipped']
                        skip_rate = (skipped / cycle_num * 100) if cycle_num > 0 else 0
                        self._status_logger.finish()  # Move to new line for summary
                        logger.info(
                            f"📊 Resumen cada 60 ciclos: {performed} updates Excel | "
                            f"{skipped} omitidas ({skip_rate:.1f}%) | "
                            f"WS: {format_number(ws_stats['messages_received'])} msgs procesados"
                        )
                    
                    # Dormir por el intervalo configurado
                    time.sleep(EXCEL_UPDATE_INTERVAL)
                    
            except KeyboardInterrupt:
                logger.info("Interrupción de teclado recibida - cerrando correctamente")
            
        except Exception as e:
            logger.error(f"Error en bucle principal de la aplicación: {e}")
        finally:
            self.shutdown()
    
    def shutdown(self):
        """Cerrar la aplicación correctamente."""
        try:
            logger.info("Cerrando aplicación...")
            
            self.is_running = False
            
            # Finish progress loggers before shutdown
            if self.sheet_operations:
                self.sheet_operations.finish_progress()
            
            if self.websocket_handler:
                self.websocket_handler.finish_progress()
            
            # Show final summary
            logger.info("\n" + "="*70)
            logger.info("📊 RESUMEN FINAL DE EJECUCIÓN")
            logger.info("="*70)
            
            self._summary_logger.show_summary("Estadísticas Finales", force=True)
            
            if self.websocket_handler:
                self.websocket_handler.show_summary(force=True)
            
            # Cerrar cliente API
            if self.api_client:
                self.api_client.close_connection()
            
            # Desconectar de Excel
            if self.workbook_manager:
                self.workbook_manager.disconnect()
            
            logger.info("="*70)
            logger.info("✅ Cierre de aplicación completado")
            
        except Exception as e:
            logger.error(f"Error durante el cierre: {e}")
    
    def get_status_report(self) -> Dict[str, Any]:
        """
        Obtener reporte de estado de la aplicación.
        
        Returns:
            dict: Información de estado
        """
        try:
            return {
                'is_running': self.is_running,
                'last_update_time': self.last_update_time,
                'last_excel_update_time': self.last_excel_update_time,
                'last_market_data_time': self.last_market_data_time,
                'excel_update_stats': self.excel_update_stats,
                'options_count': len(self.options_df),
                'securities_count': len(self.everything_df),
                'websocket_stats': self.websocket_handler.get_connection_stats() if self.websocket_handler else {},
                'processing_stats': self.data_processor.get_processing_stats() if self.data_processor else {},
                'excel_connected': self.workbook_manager.is_connected() if self.workbook_manager else False
            }
        except Exception as e:
            logger.error(f"Error al obtener reporte de estado: {e}")
            return {'error': str(e)}


def main():
    """Punto de entrada principal para la aplicación."""
    app = EPGBOptionsApp()
    app.run()


if __name__ == "__main__":
    main()