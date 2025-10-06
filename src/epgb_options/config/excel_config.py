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
