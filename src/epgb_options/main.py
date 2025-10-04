"""
Punto de entrada principal de la aplicación EPGB Options.

Este módulo provee la lógica principal de la aplicación y coordina
todos los diferentes componentes.
"""

import time
from datetime import datetime
from typing import Any, Dict

import pandas as pd

from .config import (EXCEL_FILE, EXCEL_PATH, SHEET_HOMEBROKER, SHEET_TICKERS,
                     validate_excel_config, validate_pyRofex_config)
from .excel import SheetOperations, SymbolLoader, WorkbookManager
from .market_data import DataProcessor, WebSocketHandler, pyRofexClient
from .utils import get_logger, log_connection_event, setup_logging

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
        
        # Data storage
        self.options_df = pd.DataFrame()
        self.everything_df = pd.DataFrame()
        self.cauciones_df = pd.DataFrame()
        
        # Application state
        self.is_running = False
        self.last_update_time = None
    
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
            
            # Inicializar componentes de Excel
            if not self._initialize_excel_components():
                return False
            
            # Cargar símbolos desde Excel
            if not self._load_symbols():
                return False
            
            # Inicializar componentes de datos de mercado
            if not self._initialize_market_data_components():
                return False
            
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
            tickers_sheet = self.workbook_manager.get_sheet(SHEET_TICKERS)
            if not tickers_sheet:
                logger.error(f"No se pudo acceder a la hoja {SHEET_TICKERS}")
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
            
            # Combinar otros valores (excluir cauciones de la tabla principal)
            securities_to_combine = ['acciones', 'bonos', 'cedears', 'letras', 'ons', 'panel_general']
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
                print("\033[91m⚠️  El cliente de la API PyRofex falló al inicializar\033[0m")
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
                logger.warning("⚠️  No se encontraron opciones en el caché de instrumentos")
            
            # Inicializar manejador de WebSocket con caché de instrumentos compartido (ya poblado)
            self.websocket_handler = WebSocketHandler(instrument_cache=self.api_client.instrument_cache)
            self.websocket_handler.set_data_references(self.options_df, self.everything_df, self.cauciones_df)
            self.websocket_handler.set_update_callback(self._on_data_update)
            
            # Inicializar procesador de datos
            self.data_processor = DataProcessor()
            
            # Configurar manejadores de WebSocket
            self.api_client.set_market_data_handler(self.websocket_handler.market_data_handler)
            self.api_client.set_error_handler(self.websocket_handler.websocket_error_handler)
            self.api_client.set_exception_handler(self.websocket_handler.websocket_exception_handler)
            
            # Set instrument cache in sheet operations for option detection
            self.sheet_operations.set_instrument_cache(self.api_client.instrument_cache)
            
            logger.info("✅ Componentes de datos de mercado inicializados")
            return True
            
        except Exception as e:
            logger.error(f"Error al inicializar componentes de datos de mercado: {e}")
            return False
    
    def _on_data_update(self, symbol: str, message: Dict[str, Any]):
        """
        Callback para cuando los datos de mercado se actualizan.
        
        Args:
            symbol: Símbolo actualizado
            message: Mensaje de datos de mercado
        """
        self.last_update_time = datetime.now()
        logger.debug(f"Callback de actualización de datos para {symbol}")
        
        # Podrías disparar actualizaciones de Excel acá o agruparlas
        # Por ahora, sólo registramos la actualización
    
    def start_market_data_subscription(self) -> bool:
        """Comenzar suscripción a datos de mercado."""
        try:
            logger.info("Iniciando suscripción a datos de mercado...")
            
            # Los instrumentos ya fueron cargados durante la inicialización
            # Solo necesitamos validar y suscribirnos
            
            # Suscribirse a opciones
            if not self.options_df.empty:
                options_symbols = list(self.options_df.index)
                success, valid_symbols, invalid_symbols = self.api_client.subscribe_market_data(options_symbols)
                
                if invalid_symbols:
                    logger.warning(f"Se omitieron {len(invalid_symbols)} símbolos de opciones inválidos")
                    
                if not success or not valid_symbols:
                    logger.error("Fallo al suscribirse a datos de opciones")
                    return False
                    
                logger.info(f"Suscripto a {len(valid_symbols)} opciones")
            
            # Suscribirse a otros valores  
            if not self.everything_df.empty:
                securities_symbols = list(self.everything_df.index)
                success, valid_symbols, invalid_symbols = self.api_client.subscribe_market_data(securities_symbols)
                
                if invalid_symbols:
                    logger.warning(f"Se omitieron {len(invalid_symbols)} símbolos de valores inválidos")
                    
                if not success or not valid_symbols:
                    logger.error("Fallo al suscribirse a datos de valores")
                    return False
                    
                logger.info(f"Suscripto a {len(valid_symbols)} valores")
            
            # Suscribirse a cauciones (DataFrame separado, sólo actualiza tabla derecha)
            if not self.cauciones_df.empty:
                cauciones_symbols = list(self.cauciones_df.index)
                success, valid_symbols, invalid_symbols = self.api_client.subscribe_market_data(cauciones_symbols)
                
                if invalid_symbols:
                    logger.warning(f"Se omitieron {len(invalid_symbols)} símbolos de cauciones inválidos")
                    
                if success and valid_symbols:
                    logger.info(f"Suscripto a {len(valid_symbols)} cauciones")
                else:
                    logger.warning("No hay cauciones válidas para suscribirse")
            
            log_connection_event("Suscripción a Datos de Mercado", "Iniciado exitosamente")
            return True
            
        except Exception as e:
            logger.error(f"Error al iniciar suscripción a datos de mercado: {e}")
            return False
    
    def update_excel_with_current_data(self) -> bool:
        """Actualizar Excel con los datos de mercado actuales."""
        try:
            logger.debug("Actualizando Excel con datos actuales...")
            
            # Actualizar hoja HomeBroker con datos de valores (excluyendo cauciones)
            if not self.everything_df.empty:
                success = self.sheet_operations.update_market_data_to_homebroker_sheet(
                    self.everything_df, SHEET_HOMEBROKER, self.cauciones_df
                )
                if not success:
                    logger.warning("Fallo al actualizar hoja HomeBroker")
            
            # Actualizar opciones en HomeBroker sheet
            if not self.options_df.empty:
                # Opciones usan bidsize/asksize sin underscore, necesitamos renombrar para compatibilidad con Excel
                options_for_excel = self.options_df.copy()
                options_for_excel = options_for_excel.rename(columns={'bidsize': 'bid_size', 'asksize': 'ask_size'})
                
                success = self.sheet_operations.update_market_data_to_homebroker_sheet(
                    options_for_excel, SHEET_HOMEBROKER, cauciones_df=None
                )
                if not success:
                    logger.warning("Fallo al actualizar opciones en HomeBroker")
            
            logger.debug("Actualización de Excel completada")
            return True
            
        except Exception as e:
            logger.error(f"Error al actualizar Excel: {e}")
            return False
    
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
            logger.info("Iniciando actualizaciones de Excel")
            
            # Bucle principal de la aplicación
            try:
                while self.is_running:
                    # Actualizar Excel periódicamente
                    self.update_excel_with_current_data()
                    
                    # Dormir por un intervalo corto
                    time.sleep(1)
                    
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
            
            # Cerrar cliente API
            if self.api_client:
                self.api_client.close_connection()
            
            # Desconectar de Excel
            if self.workbook_manager:
                self.workbook_manager.disconnect()
            
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