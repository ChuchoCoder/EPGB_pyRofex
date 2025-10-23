"""
Módulo de Configuración de Excel

Este módulo contiene todos los valores de configuración relacionados a Excel.
Las variables de entorno tienen prioridad sobre estos valores por defecto.

ADVERTENCIA DE SEGURIDAD: Este archivo puede contener información sensible.
Asegurate de que los permisos del archivo estén configurados (sólo lectura/escritura del propietario).

Windows: icacls excel_config.py /grant:r %USERNAME%:F /inheritance:r
"""

import os
from pathlib import Path

from dotenv import load_dotenv

# Load .env from project root
load_dotenv()

# Configuración de Excel - Las variables de entorno sobrescriben estos valores por defecto
EXCEL_FILE = os.getenv('EXCEL_FILE', 'EPGB OC-DI - Python.xlsb')
EXCEL_PATH = os.getenv('EXCEL_PATH', './')
EXCEL_SHEET_PRICES = os.getenv('EXCEL_SHEET_PRICES', 'HomeBroker')
EXCEL_SHEET_TICKERS = os.getenv('EXCEL_SHEET_TICKERS', 'Tickers')

# Intervalo de actualización de Excel en segundos
EXCEL_UPDATE_INTERVAL = float(os.getenv('EXCEL_UPDATE_INTERVAL', '3.0'))

# Trades Sheet Configuration
EXCEL_SHEET_TRADES = os.getenv('EXCEL_SHEET_TRADES', 'Trades')
TRADES_HEADER_ROW = int(os.getenv('TRADES_HEADER_ROW', '1'))
TRADES_BATCH_SIZE = int(os.getenv('TRADES_BATCH_SIZE', '500'))
TRADES_SYNC_ENABLED = os.getenv('TRADES_SYNC_ENABLED', 'true').lower() == 'true'
TRADES_REALTIME_ENABLED = os.getenv('TRADES_REALTIME_ENABLED', 'false').lower() == 'true'  # WebSocket real-time updates
TRADES_SYNC_INTERVAL_SECONDS = int(os.getenv('TRADES_SYNC_INTERVAL_SECONDS', '20'))  # 20 seconds periodic REST sync

# Column mapping (Excel column letters)
TRADES_COLUMNS = {
    'ExecutionID': 'A',
    'OrderID': 'B',
    'Account': 'C',
    'Symbol': 'D',
    'Side': 'E',
    'Quantity': 'F',
    'Price': 'G',
    'FilledQty': 'H',
    'TimestampUTC': 'I',
    'Status': 'J',
    'ExecutionType': 'K',
    'Source': 'L',
    'PreviousFilledQty': 'M',
    'PreviousTimestampUTC': 'N',
    'Superseded': 'O',
    'CancelReason': 'P',
    'UpdateCount': 'Q',
}


def validate_excel_config():
    """
    Validar valores de configuración de Excel.
    Devuelve lista de errores, lista vacía si todos son válidos.
    """
    errors = []
    
    # Verificar extensión de archivo
    if not EXCEL_FILE.lower().endswith(('.xlsx', '.xlsb', '.xlsm')):
        errors.append(f"Extensión de archivo de Excel inválida: {EXCEL_FILE}. Se esperaba .xlsx, .xlsb, o .xlsm")
    
    # Verificar si el archivo existe
    excel_file_path = os.path.join(EXCEL_PATH, EXCEL_FILE)
    if not os.path.exists(excel_file_path):
        errors.append(f"Archivo de Excel no encontrado: {excel_file_path}")
    
    # Verificar que los nombres de las hojas no estén vacíos
    if not EXCEL_SHEET_PRICES.strip():
        errors.append("EXCEL_SHEET_PRICES no puede estar vacío")
        
    if not EXCEL_SHEET_TICKERS.strip():
        errors.append("EXCEL_SHEET_TICKERS no puede estar vacío")
    
    # Verificar que EXCEL_UPDATE_INTERVAL sea un número positivo dentro de un rango razonable
    try:
        if EXCEL_UPDATE_INTERVAL <= 0:
            errors.append(f"EXCEL_UPDATE_INTERVAL debe ser un número positivo, obtenido: {EXCEL_UPDATE_INTERVAL}")
        elif EXCEL_UPDATE_INTERVAL < 0.1:
            errors.append(f"EXCEL_UPDATE_INTERVAL demasiado pequeño (mínimo: 0.1 segundos), obtenido: {EXCEL_UPDATE_INTERVAL}")
        elif EXCEL_UPDATE_INTERVAL > 60:
            errors.append(f"EXCEL_UPDATE_INTERVAL demasiado grande (máximo: 60 segundos), obtenido: {EXCEL_UPDATE_INTERVAL}")
    except (TypeError, ValueError) as e:
        errors.append(f"EXCEL_UPDATE_INTERVAL debe ser un número válido: {e}")

    # Add trades validation
    errors.extend(validate_trades_config())

    return errors


def validate_trades_config():
    """
    Validate trades-specific configuration.
    Returns list of errors, empty list if all valid.
    """
    errors = []
    
    if not EXCEL_SHEET_TRADES.strip():
        errors.append("EXCEL_SHEET_TRADES cannot be empty")
    
    if TRADES_BATCH_SIZE < 1 or TRADES_BATCH_SIZE > 10000:
        errors.append(f"TRADES_BATCH_SIZE must be 1-10000, got {TRADES_BATCH_SIZE}")
    
    if TRADES_SYNC_INTERVAL_SECONDS < 10:
        errors.append(f"TRADES_SYNC_INTERVAL_SECONDS too low (min 10s), got {TRADES_SYNC_INTERVAL_SECONDS}")
    
    # Validate column uniqueness
    col_values = list(TRADES_COLUMNS.values())
    if len(col_values) != len(set(col_values)):
        errors.append("Duplicate column mappings detected in TRADES_COLUMNS")
    
    return errors


if __name__ == "__main__":
    # Probar configuración cuando se ejecuta directamente
    errors = validate_excel_config()
    if errors:
        print("❌ Errores de configuración de Excel:")
        for error in errors:
            print(f"  - {error}")
    else:
        print("✅ La configuración de Excel es válida")
