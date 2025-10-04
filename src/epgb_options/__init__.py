"""
Aplicación de Datos de Mercado de Opciones EPGB

Una aplicación en Python para obtener y gestionar datos de mercado de opciones
con integración a Excel usando la API de pyRofex.
"""

__version__ = "1.0.0"
__author__ = "ChuchoCoder"
__email__ = "your.email@domain.com"

# Public API exports
from .main import main

__all__ = ["main"]
