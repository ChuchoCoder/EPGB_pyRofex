"""
Utilidades de validación para EPGB Options.

Este módulo provee funciones de validación de datos para datos de mercado,
símbolos, y otros datos de la aplicación.
"""

from typing import Any, Dict, List, Optional

import pandas as pd

from ..utils.logging import get_logger

logger = get_logger(__name__)


def validate_symbol(symbol: str) -> bool:
    """
    Validar un símbolo de instrumento financiero.
    
    Args:
        symbol: Símbolo a validar
        
    Returns:
        bool: True si es válido, False en caso contrario
    """
    if not symbol or not isinstance(symbol, str):
        return False
        
    # Validación básica - el símbolo no debe estar vacío después de eliminar espacios
    symbol = symbol.strip()
    if not symbol:
        return False
        
    # Pueden agregarse reglas de validación adicionales acá
    return True


def validate_market_data(data: Dict[str, Any]) -> bool:
    """
    Validar estructura de datos de mercado.
    
    Args:
        data: Diccionario de datos de mercado
        
    Returns:
        bool: True si es válido, False en caso contrario
    """
    if not isinstance(data, dict):
        logger.warning("Los datos de mercado deben ser un diccionario")
        return False
    
    # Verificar campos requeridos
    required_fields = ['instrumentId']
    missing_fields = [field for field in required_fields if field not in data]
    
    if missing_fields:
        logger.warning(f"Campos requeridos faltantes: {missing_fields}")
        return False
    
    # Validar símbolo
    symbol = data.get('instrumentId', {}).get('symbol')
    if not validate_symbol(symbol):
        logger.warning(f"Símbolo inválido: {symbol}")
        return False
    
    # Validar campos numéricos si están presentes
    numeric_fields = ['last', 'bid', 'ask', 'volume']
    for field in numeric_fields:
        if field in data:
            try:
                float(data[field])
            except (ValueError, TypeError):
                logger.warning(f"Valor numérico inválido para {field}: {data[field]}")
                return False
    
    return True


def validate_pandas_dataframe(df: pd.DataFrame, required_columns: List[str] = None) -> bool:
    """
    Validar estructura de DataFrame de pandas.
    
    Args:
        df: DataFrame a validar
        required_columns: Lista de nombres de columnas requeridas
        
    Returns:
        bool: True si es válido, False en caso contrario
    """
    if not isinstance(df, pd.DataFrame):
        logger.warning("La entrada no es un DataFrame de pandas")
        return False
    
    if df.empty:
        logger.info("DataFrame está vacío")
        return True  # Vacío es válido
    
    if required_columns:
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            logger.warning(f"Columnas requeridas faltantes: {missing_columns}")
            return False
    
    return True


def validate_excel_range_data(data: Any, allow_none: bool = True) -> bool:
    """
    Validar datos obtenidos de rangos de Excel.
    
    Args:
        data: Datos del rango de Excel
        allow_none: Si se permiten valores None
        
    Returns:
        bool: True si es válido, False en caso contrario
    """
    if data is None:
        return allow_none
    
    if isinstance(data, list):
        # Para listas, verificar cada elemento
        for item in data:
            if item is None and not allow_none:
                return False
    
    return True


def validate_configuration_values(config_dict: Dict[str, Any]) -> List[str]:
    """
    Validar valores de configuración.
    
    Args:
        config_dict: Diccionario de configuración a validar
        
    Returns:
        List[str]: Lista de mensajes de error de validación (vacía si es válido)
    """
    errors = []
    
    if not isinstance(config_dict, dict):
        errors.append("La configuración debe ser un diccionario")
        return errors
    
    # Verificar valores vacíos
    for key, value in config_dict.items():
        if value is None or (isinstance(value, str) and not value.strip()):
            errors.append(f"El valor de configuración '{key}' está vacío o es None")
    
    return errors


def safe_float_conversion(value: Any, default: float = 0.0) -> float:
    """
    Convertir un valor a float de forma segura.
    
    Args:
        value: Valor a convertir
        default: Valor por defecto si la conversión falla
        
    Returns:
        float: Valor convertido o valor por defecto
    """
    if value is None:
        return default
    
    try:
        return float(value)
    except (ValueError, TypeError):
        logger.debug(f"No se pudo convertir {value} a float, usando valor por defecto {default}")
        return default


def safe_int_conversion(value: Any, default: int = 0) -> int:
    """
    Convertir un valor a int de forma segura.
    
    Args:
        value: Valor a convertir
        default: Valor por defecto si la conversión falla
        
    Returns:
        int: Valor convertido o valor por defecto
    """
    if value is None:
        return default
    
    try:
        return int(float(value))  # Convertir mediante float para manejar strings como "123.0"
    except (ValueError, TypeError):
        logger.debug(f"No se pudo convertir {value} a int, usando valor por defecto {default}")
        return default