"""
Data processor for EPGB Options.

This module handles data transformation, aggregation, and processing
for market data received from pyRofex.
"""

import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from ..utils.logging import get_logger
from ..utils.helpers import clean_dataframe_for_excel, get_excel_safe_value
from ..utils.validation import validate_pandas_dataframe

logger = get_logger(__name__)


class DataProcessor:
    """Handles data processing and transformation for market data."""
    
    def __init__(self):
        """Initialize data processor."""
        self.last_update_time = None
        self.processing_stats = {
            'updates_processed': 0,
            'errors': 0,
            'last_processing_time': None
        }
    
    def process_securities_data(self, quotes: Any) -> pd.DataFrame:
        """
        Process securities data from pyRofex.
        
        Args:
            quotes: Securities quotes data
            
        Returns:
            pd.DataFrame: Processed securities data
        """
        try:
            logger.debug("Processing securities data")
            
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
        """Process quotes that are already in DataFrame format."""
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
            logger.error(f"Error processing DataFrame quotes: {e}")
            return quotes_df  # Return original if processing fails
    
    def _process_single_quote(self, quote: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Process a single quote message."""
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
            logger.error(f"Error processing single quote: {e}")
            return None
    
    def process_repos_data(self, quotes: Any) -> pd.DataFrame:
        """
        Process repos/cauciones data.
        
        Args:
            quotes: Repos quotes data
            
        Returns:
            pd.DataFrame: Processed repos data
        """
        try:
            logger.debug("Processing repos data")
            
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
                logger.warning("Repos data not in expected DataFrame format")
                return pd.DataFrame()
                
        except Exception as e:
            self.processing_stats['errors'] += 1
            logger.error(f"Error processing repos data: {e}")
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
                    logger.warning(f"Invalid DataFrame for {name}")
            
            if valid_dataframes:
                # Concatenate all valid DataFrames
                aggregated_df = pd.concat(valid_dataframes, ignore_index=True, sort=False)
                
                # Sort by symbol and datetime
                if 'symbol' in aggregated_df.columns:
                    aggregated_df = aggregated_df.sort_values(['symbol', 'datetime'])
                
                logger.info(f"Aggregated {len(valid_dataframes)} DataFrames into {len(aggregated_df)} rows")
                return aggregated_df
            else:
                logger.warning("No valid DataFrames to aggregate")
                return pd.DataFrame()
                
        except Exception as e:
            logger.error(f"Error aggregating market data: {e}")
            return pd.DataFrame()
    
    def calculate_derived_metrics(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate derived metrics from market data.
        
        Args:
            df: Market data DataFrame
            
        Returns:
            pd.DataFrame: DataFrame with derived metrics
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
            
            logger.debug(f"Calculated derived metrics for {len(result_df)} rows")
            return result_df
            
        except Exception as e:
            logger.error(f"Error calculating derived metrics: {e}")
            return df
    
    def filter_by_criteria(self, df: pd.DataFrame, criteria: Dict[str, Any]) -> pd.DataFrame:
        """
        Filter DataFrame based on specified criteria.
        
        Args:
            df: DataFrame to filter
            criteria: Dictionary of filter criteria
            
        Returns:
            pd.DataFrame: Filtered DataFrame
        """
        try:
            if df.empty:
                return df
            
            filtered_df = df.copy()
            
            # Apply filters based on criteria
            for column, condition in criteria.items():
                if column not in filtered_df.columns:
                    logger.warning(f"Column {column} not found for filtering")
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
            
            logger.debug(f"Filtered DataFrame from {len(df)} to {len(filtered_df)} rows")
            return filtered_df
            
        except Exception as e:
            logger.error(f"Error filtering DataFrame: {e}")
            return df
    
    def get_processing_stats(self) -> Dict[str, Any]:
        """Get processing statistics."""
        stats = self.processing_stats.copy()
        stats['last_update_time'] = self.last_update_time
        return stats
    
    def reset_stats(self):
        """Reset processing statistics."""
        self.processing_stats = {
            'updates_processed': 0,
            'errors': 0,
            'last_processing_time': datetime.now()
        }