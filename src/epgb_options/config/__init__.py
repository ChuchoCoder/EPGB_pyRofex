"""
Módulo de gestión de configuración para EPGB Options.

Este módulo proporciona gestión centralizada de la configuración con
soporte para variables de entorno usando python-dotenv.
"""

# Import all configuration variables and functions
try:
    from .excel_config import (EXCEL_FILE, EXCEL_PATH, SHEET_HOMEBROKER,
                               SHEET_TICKERS, validate_excel_config)
    from .pyrofex_config import (ACCOUNT, API_URL, ENVIRONMENT, PASSWORD, USER,
                                 WS_URL, validate_pyRofex_config)
    
    __all__ = [
        # Excel configuration
        'EXCEL_FILE', 'EXCEL_PATH', 'SHEET_HOMEBROKER', 'SHEET_TICKERS',
        'validate_excel_config',
        
        # pyRofex configuration  
        'ENVIRONMENT', 'API_URL', 'WS_URL', 'USER', 'PASSWORD', 'ACCOUNT',
        'validate_pyRofex_config'
    ]
    
except ImportError as e:
    # Graceful fallback if config modules are not available
    print(f"Advertencia: No se pudieron importar los módulos de configuración: {e}")
    __all__ = []