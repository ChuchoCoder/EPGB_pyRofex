"""
Cargador de símbolos para EPGB Options.

Este módulo carga símbolos             # Procesar datos de opciones
            if isinstance(options_data, list):
                # Filtrar valores None y strings vacíos
                valid_options = [opt for opt in options_data if opt and str(opt).strip()]
            else:
                # Valor único
                valid_options = [options_data] if options_data and str(options_data).strip() else []
            
            if not valid_options:
                logger.warning("No se encontraron opciones válidas en Excel")
                return pd.DataFrame()
            
            # Transformar símbolos para compatibilidad con pyRofexos financieros desde hojas de Excel
y los transforma para compatibilidad con pyRofex.
"""

from typing import Any, Dict, List, Optional

import pandas as pd
import xlwings as xw

from ..utils.helpers import transform_symbol_for_pyrofex
from ..utils.logging import get_logger
from ..utils.validation import validate_excel_range_data

logger = get_logger(__name__)


class SymbolLoader:
    """Carga símbolos de instrumentos financieros desde hojas de Excel."""
    
    # Mapeos de columnas para diferentes tipos de instrumentos
    COLUMN_MAPPINGS = {
        'options': 'A2:A500',      # Opciones: Columna A
        'acciones': 'C2:C500',     # Acciones: Columna C  
        'bonos': 'E2:E500',        # Bonos: Columna E
        'cedears': 'G2:G500',      # CEDEARs: Columna G
        'letras': 'I2:I500',       # Letras: Columna I
        'ons': 'K2:K500',          # ONs: Columna K
        'panel_general': 'M2:M500' # Panel General: Columna M
    }
    
    # Lista de cauciones (repos) predefinidas - sólo símbolos válidos desde la API de pyRofex
    # Nota: 1D, 2D, 7D, 8D, 9D no están disponibles en la API
    CAUCIONES = [
        "MERV - XMEV - PESOS - 3D",
        "MERV - XMEV - PESOS - 4D",
        "MERV - XMEV - PESOS - 5D",
        "MERV - XMEV - PESOS - 6D",
        "MERV - XMEV - PESOS - 10D",
        "MERV - XMEV - PESOS - 11D",
        "MERV - XMEV - PESOS - 12D",
        "MERV - XMEV - PESOS - 13D",
        "MERV - XMEV - PESOS - 14D",
    ]
    
    def __init__(self, tickers_sheet: xw.Sheet):
        """
        Inicializar cargador de símbolos.
        
        Args:
            tickers_sheet: Objeto Sheet de xlwings para la hoja Tickers
        """
        self.tickers_sheet = tickers_sheet
        self.loaded_symbols = {}
    
    def get_options_list(self) -> pd.DataFrame:
        """
        Cargar símbolos de opciones desde Excel.
        
        Returns:
            pd.DataFrame: DataFrame con datos de opciones
        """
        try:
            logger.debug("Cargando símbolos de opciones desde Excel")
            
            # Get data from Excel range
            rng = self.tickers_sheet.range(self.COLUMN_MAPPINGS['options']).expand()
            options_data = rng.value
            
            if not validate_excel_range_data(options_data):
                logger.warning("Datos de opciones inválidos desde Excel")
                return pd.DataFrame()
            
            # Procesar datos de opciones
            if isinstance(options_data, list):
                # Filter out None values and empty strings
                valid_options = [opt for opt in options_data if opt and str(opt).strip()]
            else:
                # Single value
                valid_options = [options_data] if options_data and str(options_data).strip() else []
            
            if not valid_options:
                logger.warning("No valid options found in Excel")
                return pd.DataFrame()
            
            # Transformar símbolos para compatibilidad con pyRofex
            transformed_options = [transform_symbol_for_pyrofex(opt) for opt in valid_options]
            
            # Crear DataFrame con columnas necesarias para opciones
            options_df = pd.DataFrame({
                'symbol': transformed_options,
                'bid': 0.0,
                'ask': 0.0,
                'bidsize': 0,
                'asksize': 0,
                'last': 0.0,
                'change': 0.0,
                'volume': 0,
                'datetime': pd.Timestamp.now()
            })
            
            options_df.set_index('symbol', inplace=True)
            
            self.loaded_symbols['options'] = options_df
            logger.info(f"Cargados {len(options_df)} símbolos de opciones")
            
            return options_df
            
        except Exception as e:
            logger.error(f"Error al cargar lista de opciones: {e}")
            return pd.DataFrame()
    
    def get_acciones_list(self) -> pd.DataFrame:
        """
        Cargar símbolos de acciones desde Excel.
        
        Returns:
            pd.DataFrame: DataFrame con datos de acciones
        """
        return self._load_securities_list('acciones', 'acciones')
    
    def get_bonos_list(self) -> pd.DataFrame:
        """
        Cargar símbolos de bonos desde Excel.
        
        Returns:
            pd.DataFrame: DataFrame con datos de bonos
        """
        return self._load_securities_list('bonos', 'bonos')
    
    def get_cedears_list(self) -> pd.DataFrame:
        """
        Cargar símbolos de CEDEARs desde Excel.
        
        Returns:
            pd.DataFrame: DataFrame con datos de CEDEARs
        """
        return self._load_securities_list('cedears', 'CEDEARs')
    
    def get_letras_list(self) -> pd.DataFrame:
        """
        Cargar símbolos de letras desde Excel.
        
        Returns:
            pd.DataFrame: DataFrame con datos de letras
        """
        return self._load_securities_list('letras', 'letras')
    
    def get_ons_list(self) -> pd.DataFrame:
        """
        Cargar símbolos de ONs desde Excel.
        
        Returns:
            pd.DataFrame: DataFrame con datos de ONs
        """
        return self._load_securities_list('ons', 'ONs')
    
    def get_panel_general_list(self) -> pd.DataFrame:
        """
        Cargar símbolos de Panel General desde Excel.
        
        Returns:
            pd.DataFrame: DataFrame con datos de Panel General
        """
        return self._load_securities_list('panel_general', 'Panel General')
    
    def get_cauciones_list(self) -> pd.DataFrame:
        """
        Obtener lista predefinida de cauciones (repos).
        
        Returns:
            pd.DataFrame: DataFrame con datos de cauciones
        """
        try:
            logger.debug("Creando lista de cauciones")
            
            # Crear DataFrame con cauciones predefinidas
            # Coincidir con las columnas esperadas por el layout de Excel (columnas B-O)
            cauciones_df = pd.DataFrame({
                'symbol': self.CAUCIONES,
                'bid_size': 0,
                'bid': 0.0,
                'ask': 0.0,
                'ask_size': 0,
                'last': 0.0,
                'change': 0.0,
                'open': 0.0,
                'high': 0.0,
                'low': 0.0,
                'previous_close': 0.0,
                'turnover': 0.0,
                'volume': 0,
                'operations': 0,
                'datetime': pd.Timestamp.now()
            })
            
            cauciones_df.set_index('symbol', inplace=True)
            
            self.loaded_symbols['cauciones'] = cauciones_df
            logger.info(f"Creados {len(cauciones_df)} símbolos de cauciones")
            
            return cauciones_df
            
        except Exception as e:
            logger.error(f"Error al crear lista de cauciones: {e}")
            return pd.DataFrame()
    
    def _load_securities_list(self, instrument_type: str, display_name: str) -> pd.DataFrame:
        """
        Método genérico para cargar títulos desde Excel.
        
        Args:
            instrument_type: Clave para mapeo de columna
            display_name: Nombre legible para logging
            
        Returns:
            pd.DataFrame: DataFrame con datos de títulos
        """
        try:
            logger.debug(f"Cargando símbolos de {display_name} desde Excel")
            
            if instrument_type not in self.COLUMN_MAPPINGS:
                logger.error(f"Tipo de instrumento desconocido: {instrument_type}")
                return pd.DataFrame()
            
            # Obtener datos desde rango de Excel
            rng = self.tickers_sheet.range(self.COLUMN_MAPPINGS[instrument_type]).expand()
            securities_data = rng.value
            
            if not validate_excel_range_data(securities_data):
                logger.warning(f"Datos de {display_name} inválidos desde Excel")
                return pd.DataFrame()
            
            # Procesar datos de títulos
            if isinstance(securities_data, list):
                # Filtrar valores None y strings vacíos
                valid_securities = [sec for sec in securities_data if sec and str(sec).strip()]
            else:
                # Valor único
                valid_securities = [securities_data] if securities_data and str(securities_data).strip() else []
            
            if not valid_securities:
                logger.warning(f"No se encontraron {display_name} válidos en Excel")
                return pd.DataFrame()
            
            # Transformar símbolos para compatibilidad con pyRofex
            transformed_securities = [transform_symbol_for_pyrofex(sec) for sec in valid_securities]
            
            # Crear DataFrame con columnas necesarias para títulos
            # Coincidir con las columnas esperadas por el layout de Excel (columnas B-O)
            securities_df = pd.DataFrame({
                'symbol': transformed_securities,
                'bid_size': 0,
                'bid': 0.0,
                'ask': 0.0,
                'ask_size': 0,
                'last': 0.0,
                'change': 0.0,
                'open': 0.0,
                'high': 0.0,
                'low': 0.0,
                'previous_close': 0.0,
                'turnover': 0.0,
                'volume': 0,
                'operations': 0,
                'datetime': pd.Timestamp.now()
            })
            
            securities_df.set_index('symbol', inplace=True)
            
            self.loaded_symbols[instrument_type] = securities_df
            logger.info(f"Cargados {len(securities_df)} símbolos de {display_name}")
            
            return securities_df
            
        except Exception as e:
            logger.error(f"Error al cargar lista de {display_name}: {e}")
            return pd.DataFrame()
    
    def get_all_symbols(self) -> Dict[str, pd.DataFrame]:
        """
        Cargar todos los tipos de símbolos desde Excel.
        
        Returns:
            dict: Diccionario de DataFrames para cada tipo de instrumento
        """
        try:
            logger.info("Cargando todos los símbolos desde Excel")
            
            all_symbols = {
                'options': self.get_options_list(),
                'acciones': self.get_acciones_list(),
                'bonos': self.get_bonos_list(),
                'cedears': self.get_cedears_list(),
                'letras': self.get_letras_list(),
                'ons': self.get_ons_list(),
                'panel_general': self.get_panel_general_list(),
                'cauciones': self.get_cauciones_list()
            }
            
            # Resumen de log
            total_symbols = sum(len(df) for df in all_symbols.values())
            logger.info(f"Cargado un total de {total_symbols} símbolos en todos los tipos de instrumentos")
            
            return all_symbols
            
        except Exception as e:
            logger.error(f"Error al cargar todos los símbolos: {e}")
            return {}
    
    def get_combined_securities(self) -> pd.DataFrame:
        """
        Obtener DataFrame combinado de todos los títulos (excluyendo opciones).
        
        Returns:
            pd.DataFrame: DataFrame de títulos combinados
        """
        try:
            securities_dfs = [
                self.get_acciones_list(),
                self.get_bonos_list(), 
                self.get_cedears_list(),
                self.get_letras_list(),
                self.get_ons_list(),
                self.get_panel_general_list(),
                self.get_cauciones_list()
            ]
            
            # Filtrar DataFrames vacíos
            valid_dfs = [df for df in securities_dfs if not df.empty]
            
            if valid_dfs:
                combined_df = pd.concat(valid_dfs, ignore_index=False)
                logger.info(f"Combinados {len(combined_df)} símbolos de títulos")
                return combined_df
            else:
                logger.warning("No hay datos de títulos válidos para combinar")
                return pd.DataFrame()
                
        except Exception as e:
            logger.error(f"Error al combinar títulos: {e}")
            return pd.DataFrame()
    
    def get_symbol_count_by_type(self) -> Dict[str, int]:
        """
        Obtener conteo de símbolos por tipo de instrumento.
        
        Returns:
            dict: Conteos de símbolos por tipo
        """
        counts = {}
        for instrument_type, df in self.loaded_symbols.items():
            counts[instrument_type] = len(df) if not df.empty else 0
        
        return counts