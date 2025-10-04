"""
Utilidades de logging para EPGB Options.

Este módulo provee configuración centralizada de logging y utilidades.
"""

import logging
import sys
from datetime import datetime
from pathlib import Path


def setup_logging(level=logging.INFO, log_file=None):
    """
    Configurar logging.
    
    Args:
        level: Nivel de logging (por defecto: INFO)
        log_file: Ruta opcional del archivo de log
    """
    # Crear formateador
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Configurar logger raíz
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    
    # Limpiar manejadores existentes
    root_logger.handlers.clear()
    
    # Manejador de consola
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)
    
    # Manejador de archivo (si se especifica)
    if log_file:
        # Crear directorio de log si no existe
        Path(log_file).parent.mkdir(parents=True, exist_ok=True)
        
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)


def get_logger(name):
    """
    Obtener un logger con el nombre especificado.
    
    Args:
        name: Nombre del logger (típicamente __name__)
        
    Returns:
        logging.Logger: Logger configurado
    """
    return logging.getLogger(name)


def log_validation_message(category, message, success=None):
    """
    Registrar un mensaje de validación con formato consistente.
    
    Args:
        category: Categoría de validación
        message: Mensaje de validación
        success: True si fue exitoso, False si falló, None para info
    """
    logger = get_logger("validation")
    
    if success is True:
        logger.info(f"✅ {category}: {message}")
    elif success is False:
        logger.error(f"❌ {category}: {message}")
    else:
        logger.info(f"ℹ️ {category}: {message}")


def log_connection_event(event_type, details=""):
    """
    Registrar eventos relacionados a conexiones.
    
    Args:
        event_type: Tipo de evento de conexión
        details: Detalles adicionales
    """
    logger = get_logger("connection")
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    if details:
        logger.info(f"[{timestamp}] {event_type}: {details}")
    else:
        logger.info(f"[{timestamp}] {event_type}")


def log_market_data_event(symbol, event_type, data=None):
    """
    Registrar eventos de datos de mercado.
    
    Args:
        symbol: Símbolo de instrumento financiero
        event_type: Tipo de evento de datos de mercado  
        data: Datos de mercado opcionales
    """
    logger = get_logger("market_data")
    
    if data:
        logger.debug(f"Evento: {symbol} - {event_type}: {data}")
    else:
        logger.debug(f"Evento: {symbol} - {event_type}")