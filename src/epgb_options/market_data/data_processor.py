"""
Procesador de datos para EPGB Options.

Este módulo maneja la transformación, agregación y procesamiento de datos
para datos de mercado recibidos desde pyRofex.
"""

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import pandas as pd

from ..utils.helpers import clean_dataframe_for_excel, get_excel_safe_value
from ..utils.logging import get_logger
from ..utils.validation import validate_pandas_dataframe

logger = get_logger(__name__)


class DataProcessor:
    """Maneja procesamiento y transformación de datos para datos de mercado."""
    
    def __init__(self):
        """Inicializar procesador de datos."""
        self.last_update_time = None
        self.processing_stats = {
            'updates_processed': 0,
            'errors': 0,
            'last_processing_time': None
        }
    
    def process_securities_data(self, quotes: Any) -> pd.DataFrame:
        """
        Procesar datos de valores desde pyRofex.
        
        Args:
            quotes: Datos de cotizaciones de valores
            
        Returns:
            pd.DataFrame: Datos de valores procesados
        """
        try:
            logger.debug("Procesando datos de valores")
            
            # Handle both single message and multiple messages
            if isinstance(quotes, dict):
                quotes_list = [quotes]
            elif isinstance(quotes, list):
                quotes_list = quotes
            elif isinstance(quotes, pd.DataFrame):
                return self._process_dataframe_quotes(quotes)
            else:
                logger.warning(f"Unknown quotes format: {type(quotes)}")
                return pd.DataFrame()
            
            # Process each quote
            processed_rows = []
            for quote in quotes_list:
                if isinstance(quote, dict):
                    processed_row = self._process_single_quote(quote)
                    if processed_row is not None:
                        processed_rows.append(processed_row)
            
            if processed_rows:
                result_df = pd.DataFrame(processed_rows)
                self.processing_stats['updates_processed'] += len(processed_rows)
                return result_df
            else:
                return pd.DataFrame()
                
        except Exception as e:
            self.processing_stats['errors'] += 1
            logger.error(f"Error processing securities data: {e}")
            return pd.DataFrame()
    
    def _process_dataframe_quotes(self, quotes_df: pd.DataFrame) -> pd.DataFrame:
        """Procesar cotizaciones que ya están en formato DataFrame."""
        try:
            # Apply standard transformations
            processed_df = quotes_df.copy()
            
            # Apply change percentage conversion (if change column exists)
            if 'change' in processed_df.columns:
                processed_df['change'] = processed_df['change'] / 100
            
            # Ensure datetime column is properly formatted
            if 'datetime' in processed_df.columns:
                processed_df['datetime'] = pd.to_datetime(processed_df['datetime'])
            else:
                processed_df['datetime'] = pd.Timestamp.now()
            
            # Clean data for Excel compatibility
            processed_df = clean_dataframe_for_excel(processed_df)
            
            return processed_df
            
        except Exception as e:
            logger.error(f"Error al procesar cotizaciones en DataFrame: {e}")
            return quotes_df  # Return original if processing fails
    
    def _process_single_quote(self, quote: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Procesar un mensaje de cotización individual."""
        try:
            # Extract symbol information
            symbol = quote.get('instrumentId', {}).get('symbol', 'UNKNOWN')
            
            # Extract market data
            market_data = quote.get('marketData', {})
            
            # Process standard fields
            processed_quote = {
                'symbol': symbol,
                'bid': get_excel_safe_value(market_data.get('BI')),
                'ask': get_excel_safe_value(market_data.get('OF')),
                'bid_size': get_excel_safe_value(market_data.get('BI_size')),
                'ask_size': get_excel_safe_value(market_data.get('OF_size')),
                'last': get_excel_safe_value(market_data.get('LA')),
                'change': get_excel_safe_value(market_data.get('CH', 0)) / 100,  # Convert to percentage
                'open': get_excel_safe_value(market_data.get('OP')),
                'high': get_excel_safe_value(market_data.get('HI')),
                'low': get_excel_safe_value(market_data.get('LO')),
                'previous_close': get_excel_safe_value(market_data.get('CL')),
                'turnover': get_excel_safe_value(market_data.get('TV')),
                'volume': get_excel_safe_value(market_data.get('EV')),
                'operations': get_excel_safe_value(market_data.get('NV')),
                'datetime': pd.Timestamp.now()
            }
            
            return processed_quote
            
        except Exception as e:
            logger.error(f"Error al procesar cotización individual: {e}")
            return None
    
    def process_repos_data(self, quotes: Any) -> pd.DataFrame:
        """
        Procesar datos de repos/cauciones.
        
        Args:
            quotes: Datos de cotizaciones de repos
            
        Returns:
            pd.DataFrame: Datos de repos procesados
        """
        try:
            logger.debug("Procesando datos de cauciones")
            
            # Similar processing to securities but with repos-specific logic
            if isinstance(quotes, pd.DataFrame):
                processed_df = quotes.copy()
                
                # Apply repos-specific transformations
                if 'change' in processed_df.columns:
                    processed_df['change'] = processed_df['change'] / 100
                
                if 'datetime' in processed_df.columns:
                    processed_df['datetime'] = pd.to_datetime(processed_df['datetime'])
                else:
                    processed_df['datetime'] = pd.Timestamp.now()
                
                # Clean for Excel
                processed_df = clean_dataframe_for_excel(processed_df)
                
                self.processing_stats['updates_processed'] += len(processed_df)
                return processed_df
            else:
                logger.warning("Datos de cauciones no están en el formato DataFrame esperado")
                return pd.DataFrame()
                
        except Exception as e:
            self.processing_stats['errors'] += 1
            logger.error(f"Error al procesar datos de cauciones: {e}")
            return pd.DataFrame()
    
    def aggregate_market_data(self, data_dict: Dict[str, pd.DataFrame]) -> pd.DataFrame:
        """
        Aggregate multiple DataFrames into a single consolidated DataFrame.
        
        Args:
            data_dict: Dictionary of DataFrames to aggregate
            
        Returns:
            pd.DataFrame: Aggregated DataFrame
        """
        try:
            valid_dataframes = []
            
            for name, df in data_dict.items():
                if validate_pandas_dataframe(df):
                    if not df.empty:
                        # Add source column to track data origin
                        df_copy = df.copy()
                        df_copy['data_source'] = name
                        valid_dataframes.append(df_copy)
                else:
                    logger.warning(f"DataFrame inválido para {name}")
            
            if valid_dataframes:
                # Concatenate all valid DataFrames
                aggregated_df = pd.concat(valid_dataframes, ignore_index=True, sort=False)
                
                # Sort by symbol and datetime
                if 'symbol' in aggregated_df.columns:
                    aggregated_df = aggregated_df.sort_values(['symbol', 'datetime'])
                
                logger.info(f"Agregados {len(valid_dataframes)} DataFrames en {len(aggregated_df)} filas")
                return aggregated_df
            else:
                logger.warning("No hay DataFrames válidos para agregar")
                return pd.DataFrame()
                
        except Exception as e:
            logger.error(f"Error al agregar datos de mercado: {e}")
            return pd.DataFrame()
    
    def calculate_derived_metrics(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Calcular métricas derivadas a partir de datos de mercado.
        
        Args:
            df: DataFrame con datos de mercado
            
        Returns:
            pd.DataFrame: DataFrame con métricas derivadas
        """
        try:
            if df.empty:
                return df
            
            result_df = df.copy()
            
            # Calculate spread
            if 'ask' in result_df.columns and 'bid' in result_df.columns:
                result_df['spread'] = result_df['ask'] - result_df['bid']
                result_df['spread_pct'] = (result_df['spread'] / result_df['bid']) * 100
            
            # Calculate price change percentage
            if 'last' in result_df.columns and 'previous_close' in result_df.columns:
                result_df['price_change_pct'] = ((result_df['last'] - result_df['previous_close']) / result_df['previous_close']) * 100
            
            # Calculate volatility indicators (simplified)
            if all(col in result_df.columns for col in ['high', 'low', 'last']):
                result_df['volatility_range'] = result_df['high'] - result_df['low']
                result_df['volatility_pct'] = (result_df['volatility_range'] / result_df['last']) * 100
            
            logger.debug(f"Calculadas métricas derivadas para {len(result_df)} filas")
            return result_df
            
        except Exception as e:
            logger.error(f"Error al calcular métricas derivadas: {e}")
            return df
    
    def filter_by_criteria(self, df: pd.DataFrame, criteria: Dict[str, Any]) -> pd.DataFrame:
        """
        Filtrar un DataFrame según criterios especificados.
        
        Args:
            df: DataFrame a filtrar
            criteria: Diccionario con criterios de filtrado
            
        Returns:
            pd.DataFrame: DataFrame filtrado
        """
        try:
            if df.empty:
                return df
            
            filtered_df = df.copy()
            
            # Apply filters based on criteria
            for column, condition in criteria.items():
                if column not in filtered_df.columns:
                    logger.warning(f"Columna {column} no encontrada para filtrar")
                    continue
                
                if isinstance(condition, dict):
                    # Handle range conditions
                    if 'min' in condition:
                        filtered_df = filtered_df[filtered_df[column] >= condition['min']]
                    if 'max' in condition:
                        filtered_df = filtered_df[filtered_df[column] <= condition['max']]
                elif isinstance(condition, (list, tuple)):
                    # Handle list of values
                    filtered_df = filtered_df[filtered_df[column].isin(condition)]
                else:
                    # Handle single value
                    filtered_df = filtered_df[filtered_df[column] == condition]
            
            logger.debug(f"Filtrado DataFrame de {len(df)} a {len(filtered_df)} filas")
            return filtered_df
            
        except Exception as e:
            logger.error(f"Error al filtrar DataFrame: {e}")
            return df
    
    def get_processing_stats(self) -> Dict[str, Any]:
        """Obtener estadísticas de procesamiento."""
        stats = self.processing_stats.copy()
        stats['last_update_time'] = self.last_update_time
        return stats
    
    def reset_stats(self):
        """Reiniciar estadísticas de procesamiento."""
        self.processing_stats = {
            'updates_processed': 0,
            'errors': 0,
            'last_processing_time': datetime.now()
        }