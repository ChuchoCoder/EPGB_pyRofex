"""
Operaciones de hojas de Excel para EPGB Options.

Este módulo maneja lectura y escritura en hojas de Excel,
incluyendo actualizaciones de datos y formato.
"""

from typing import Any, Dict, List, Optional, Union

import pandas as pd
import xlwings as xw

from ..utils.helpers import (clean_dataframe_for_excel,
                             clean_symbol_for_display, get_excel_safe_value,
                             restore_symbol_prefix)
from ..utils.logging import get_logger
from ..utils.validation import validate_pandas_dataframe

logger = get_logger(__name__)


class SheetOperations:
    """Maneja operaciones de hojas de Excel para lectura y escritura de datos."""
    
    def __init__(self, workbook: xw.Book, instrument_cache=None):
        """
        Inicializar operaciones de hojas.
        
        Args:
            workbook: Objeto Workbook de xlwings
            instrument_cache: Instancia opcional de InstrumentCache para detección de opciones
        """
        self.workbook = workbook
        self.instrument_cache = instrument_cache
        self.update_stats = {
            'updates_performed': 0,
            'errors': 0,
            'last_update_time': None
        }
    
    def set_instrument_cache(self, instrument_cache):
        """
        Establecer el caché de instrumentos para detección de opciones.
        
        Args:
            instrument_cache: Instancia de InstrumentCache
        """
        self.instrument_cache = instrument_cache
        logger.debug("Caché de instrumentos configurado para detección de opciones")
    
    def read_range(self, sheet_name: str, range_address: str) -> Any:
        """
        Leer datos de un rango de Excel.
        
        Args:
            sheet_name: Nombre de la hoja
            range_address: Dirección del rango de Excel (ej., 'A1:C10')
            
        Returns:
            Any: Datos del rango
        """
        try:
            sheet = self.workbook.sheets(sheet_name)
            data = sheet.range(range_address).value
            logger.debug(f"Datos leídos de {sheet_name}!{range_address}")
            return data
        except Exception as e:
            logger.error(f"Error al leer el rango {sheet_name}!{range_address}: {e}")
            return None
    
    def write_range(self, sheet_name: str, range_address: str, data: Any) -> bool:
        """
        Escribir datos en un rango de Excel.
        
        Args:
            sheet_name: Nombre de la hoja
            range_address: Dirección del rango de Excel
            data: Datos a escribir
            
        Returns:
            bool: True si fue exitoso, False en caso contrario
        """
        try:
            sheet = self.workbook.sheets(sheet_name)
            sheet.range(range_address).value = data
            logger.debug(f"Datos escritos en {sheet_name}!{range_address}")
            self.update_stats['updates_performed'] += 1
            return True
        except Exception as e:
            logger.error(f"Error al escribir en el rango {sheet_name}!{range_address}: {e}")
            self.update_stats['errors'] += 1
            return False
    
    def update_dataframe_to_sheet(self, sheet_name: str, df: pd.DataFrame, 
                                  start_cell: str = 'A1', include_index: bool = True,
                                  include_header: bool = True) -> bool:
        """
        Escribir DataFrame en una hoja de Excel.
        
        Args:
            sheet_name: Nombre de la hoja
            df: DataFrame a escribir
            start_cell: Celda inicial para los datos
            include_index: Si se debe incluir el índice del DataFrame
            include_header: Si se debe incluir el encabezado del DataFrame
            
        Returns:
            bool: True si fue exitoso, False en caso contrario
        """
        try:
            if not validate_pandas_dataframe(df):
                logger.error("DataFrame inválido para actualización de hoja")
                return False
            
            if df.empty:
                logger.warning("DataFrame vacío - nada que actualizar")
                return True
            
            # Clean DataFrame for Excel compatibility
            clean_df = clean_dataframe_for_excel(df)
            
            # Get sheet
            sheet = self.workbook.sheets(sheet_name)
            
            # Write DataFrame to sheet
            sheet.range(start_cell).options(pd.DataFrame, 
                                           index=include_index, 
                                           header=include_header).value = clean_df
            
            logger.info(f"Actualizada {sheet_name} con {len(clean_df)} filas de datos")
            self.update_stats['updates_performed'] += 1
            return True
            
        except Exception as e:
            logger.error(f"Error al actualizar DataFrame en {sheet_name}: {e}")
            self.update_stats['errors'] += 1
            return False
    
    def update_market_data_to_homebroker_sheet(self, df: pd.DataFrame, 
                                               homebroker_sheet_name: str,
                                               cauciones_df: pd.DataFrame = None) -> bool:
        """
        Actualizar datos de mercado en la hoja HomeBroker con formato específico.
        Utiliza actualización de rango masiva para máxima performance.
        
        Args:
            df: DataFrame con datos de mercado (excluyendo cauciones)
            homebroker_sheet_name: Nombre de la hoja HomeBroker
            cauciones_df: DataFrame opcional con datos de cauciones (actualiza solo tabla derecha)
            
        Returns:
            bool: True si fue exitoso, False en caso contrario
        """
        try:
            if df.empty:
                logger.warning("No hay datos de mercado para actualizar")
                return True
            
            logger.debug(f"Actualizando datos de mercado en {homebroker_sheet_name}")
            
            # DEBUG: Log DataFrame state for first few updates
            if self.update_stats['updates_performed'] < 2:
                sample_symbols = df.index[:3].tolist()
                logger.debug(f"Muestra de DataFrame (primeros 3 símbolos): {sample_symbols}")
                for sym in sample_symbols:
                    logger.debug(f"  {sym}: bid={df.loc[sym, 'bid']}, ask={df.loc[sym, 'ask']}, last={df.loc[sym, 'last']}")
            
            # Get HomeBroker sheet
            homebroker_sheet = self.workbook.sheets(homebroker_sheet_name)
            
            # Build symbol-to-row mapping ONCE (cache for performance)
            if not hasattr(self, '_symbol_row_cache') or self.update_stats['updates_performed'] == 0:
                # Ensure headers exist in row 1
                self._ensure_headers_exist(homebroker_sheet)
                
                # Read existing symbols from column A (skip header row)
                symbols_range = homebroker_sheet.range('A2:A1000')  # Read up to 1000 rows
                symbols = symbols_range.value
                
                # Handle case where only one symbol exists (xlwings returns single value instead of list)
                if not isinstance(symbols, list):
                    symbols = [symbols] if symbols else []
                
                self._symbol_row_cache = {}
                duplicate_rows = []  # Track rows with duplicate symbols
                
                for idx, cell_value in enumerate(symbols):
                    if cell_value and str(cell_value).strip():
                        # Row index is idx + 2 (skip header at row 1, and enumerate starts at 0)
                        # Cell contains cleaned symbol (e.g., "GGAL - 24hs" or "GFGC73354O")
                        display_symbol = str(cell_value).strip()
                        
                        # Restore prefix first
                        full_symbol = restore_symbol_prefix(display_symbol)
                        
                        # Check if symbol already has a suffix (e.g., " - 24hs", " - 48hs", etc.)
                        has_suffix = any(full_symbol.endswith(suffix) for suffix in 
                                       [" - 24hs", " - 48hs", " - 72hs", " - CI", " - T0", " - T1", " - T2"])
                        
                        # If no suffix present and not a caucion (PESOS - XD), add " - 24hs"
                        # This handles options that had their suffix stripped for display
                        if not has_suffix and "PESOS" not in full_symbol:
                            full_symbol = f"{full_symbol} - 24hs"
                        
                        # Check for duplicates
                        if full_symbol in self._symbol_row_cache:
                            duplicate_rows.append(idx + 2)
                            logger.warning(f"Símbolo duplicado detectado: {display_symbol} en fila {idx + 2} (ya existe en fila {self._symbol_row_cache[full_symbol]})")
                        else:
                            self._symbol_row_cache[full_symbol] = idx + 2
                
                logger.info(f"Caché de filas de símbolos construido con {len(self._symbol_row_cache)} símbolos desde Excel")
                
                # If duplicates found, clean them up
                if duplicate_rows:
                    logger.warning(f"Encontradas {len(duplicate_rows)} símbolos duplicados en la hoja de Excel")
                    self._remove_duplicate_rows(homebroker_sheet, duplicate_rows)
                    logger.info(f"✅ Eliminadas {len(duplicate_rows)} filas duplicadas de Excel")
            
            # Always check for missing symbols (not just on first call)
            # This ensures options (or any new symbols) added later are also populated
            missing_symbols = [sym for sym in df.index if sym not in self._symbol_row_cache]
            if missing_symbols:
                logger.info(f"Auto-poblando {len(missing_symbols)} símbolos nuevos en la hoja HomeBroker...")
                self._add_symbols_to_sheet(homebroker_sheet, missing_symbols)
                logger.info(f"✅ Agregados {len(missing_symbols)} símbolos nuevos a Excel")
            
            # BULK UPDATE: Build 2D array for all data at once
            # Columns: B=bid_size, C=bid, D=ask, E=ask_size, F=last, G=change, H=open, I=high, J=low, K=previous_close, L=turnover, M=volume, N=operations, O=datetime
            field_order = ['bid_size', 'bid', 'ask', 'ask_size', 'last', 'change', 'open', 
                          'high', 'low', 'previous_close', 'turnover', 'volume', 'operations', 'datetime']
            
            # Collect updates by row number
            updates_by_row = {}
            for symbol, row_data in df.iterrows():
                row_index = self._symbol_row_cache.get(symbol)
                if row_index:
                    # Build row values
                    row_values = []
                    for field in field_order:
                        if field in row_data:
                            row_values.append(get_excel_safe_value(row_data[field]))
                        else:
                            row_values.append(0)
                    updates_by_row[row_index] = row_values
            
            # Find contiguous ranges for even faster bulk updates
            sorted_rows = sorted(updates_by_row.keys())
            if sorted_rows:
                min_row = sorted_rows[0]
                max_row = sorted_rows[-1]
                
                # Build 2D array with all rows (including gaps filled with existing data)
                bulk_data = []
                for row_idx in range(min_row, max_row + 1):
                    if row_idx in updates_by_row:
                        bulk_data.append(updates_by_row[row_idx])
                    else:
                        # Keep existing data for rows not in DataFrame (fill with None to skip update)
                        bulk_data.append([None] * len(field_order))
                
                # Single bulk write: Write entire range B{min}:O{max} at once
                range_address = f'B{min_row}:O{max_row}'
                homebroker_sheet.range(range_address).value = bulk_data
                
                logger.info(f"✅ Actualización masiva de {len(updates_by_row)} instrumentos en el rango {range_address}")
            
            # Update cauciones table on the right side (columns R-U) using separate DataFrame
            if cauciones_df is not None and not cauciones_df.empty:
                self._update_cauciones_table(homebroker_sheet, cauciones_df)
            
            self.update_stats['updates_performed'] += 1
            return True
            
        except Exception as e:
            logger.error(f"Error al actualizar datos de mercado en la hoja HomeBroker: {e}")
            self.update_stats['errors'] += 1
            return False
    
    def _ensure_headers_exist(self, sheet: xw.Sheet):
        """
        Asegurar que la hoja HomeBroker tenga los encabezados apropiados en la fila 1.
        
        Args:
            sheet: Objeto Sheet de xlwings
        """
        try:
            # Check if headers already exist
            header_row = sheet.range('A1:O1').value
            
            # Define expected headers
            expected_headers = [
                'symbol', 'bid_size', 'bid', 'ask', 'ask_size', 'last', 'change',
                'open', 'high', 'low', 'previous_close', 'turnover', 'volume',
                'operations', 'datetime'
            ]
            
            # If headers don't match, write them
            if not header_row or header_row[0] != 'symbol':
                logger.info("Creando encabezados en la hoja HomeBroker...")
                sheet.range('A1:O1').value = expected_headers
                # Optional: Format headers (bold)
                sheet.range('A1:O1').font.bold = True
                logger.debug("Encabezados creados exitosamente")
                
        except Exception as e:
            logger.error(f"Error al asegurar que existan los encabezados: {e}")
            raise
    
    def _remove_duplicate_rows(self, sheet: xw.Sheet, row_numbers: list):
        """
        Eliminar filas duplicadas de la hoja de Excel.
        
        Args:
            sheet: Objeto Sheet de xlwings
            row_numbers: Lista de números de fila a eliminar (debe estar ordenada descendentemente)
        """
        try:
            if not row_numbers:
                return
            
            # Sort in descending order to delete from bottom to top
            # This prevents row number shifting during deletion
            sorted_rows = sorted(row_numbers, reverse=True)
            
            logger.info(f"Eliminando {len(sorted_rows)} filas duplicadas de Excel...")
            
            for row_num in sorted_rows:
                # Delete the entire row
                sheet.range(f'{row_num}:{row_num}').api.Delete()
            
            logger.debug(f"Eliminadas exitosamente {len(sorted_rows)} filas duplicadas")
            
        except Exception as e:
            logger.error(f"Error al eliminar filas duplicadas: {e}")
            raise
    
    def _add_symbols_to_sheet(self, sheet: xw.Sheet, symbols: list):
        """
        Agregar nuevos símbolos a la hoja HomeBroker.
        
        Args:
            sheet: Objeto Sheet de xlwings
            symbols: Lista de símbolos a agregar
        """
        try:
            # Find the last row with data in column A (starting from row 2, since row 1 is header)
            last_row = 1  # Start with header row
            if hasattr(self, '_symbol_row_cache') and self._symbol_row_cache:
                last_row = max(self._symbol_row_cache.values())
            else:
                # Check for existing data starting from row 2
                existing_symbols = sheet.range('A2:A1000').value
                if isinstance(existing_symbols, list):
                    # Count non-empty cells
                    non_empty = [s for s in existing_symbols if s and str(s).strip()]
                    last_row = len(non_empty) + 1  # +1 for header
                elif existing_symbols:
                    last_row = 2  # One symbol at row 2
            
            # Add symbols starting from the next available row
            start_row = last_row + 1
            
            # Prepare bulk data for faster writing
            symbol_data = []
            for i, symbol in enumerate(symbols):
                row_num = start_row + i
                
                # Check if symbol is an option (for proper display formatting)
                is_option = False
                if self.instrument_cache:
                    is_option = self.instrument_cache.is_option_symbol(symbol)
                
                # Clean symbol for display (remove "MERV - XMEV - " prefix, and " - 24hs" for options)
                display_symbol = clean_symbol_for_display(symbol, is_option=is_option)
                
                # Prepare row: [symbol, bid_size, bid, ask, ask_size, last, change, open, high, low, previous_close, turnover, volume, operations, datetime]
                row_data = [display_symbol] + [0] * 13 + ['']  # 13 numeric columns + 1 datetime column
                symbol_data.append(row_data)
                
                # Update cache with ORIGINAL symbol (for lookups), but display cleaned version
                self._symbol_row_cache[symbol] = row_num
            
            # Bulk write all symbols at once (much faster than individual writes)
            end_row = start_row + len(symbols) - 1
            sheet.range(f'A{start_row}:O{end_row}').value = symbol_data
            
            logger.debug(f"Agregados {len(symbols)} símbolos a la hoja comenzando en fila {start_row}")
            
        except Exception as e:
            logger.error(f"Error al agregar símbolos a la hoja: {e}")
            raise
    
    def _update_cauciones_table(self, sheet: xw.Sheet, df: pd.DataFrame):
        """
        Actualizar la tabla de cauciones en el lado derecho de la hoja HomeBroker.
        
        La tabla tiene Plazo (Período) en la columna R comenzando desde la fila 2:
        - Fila 2: "1 día" -> MERV - XMEV - PESOS - 1D (si existe)
        - Fila 4: "3 días" -> MERV - XMEV - PESOS - 3D
        - Fila 5: "4 días" -> MERV - XMEV - PESOS - 4D
        - etc.
        
        Columnas a actualizar:
        - R: Plazo (período como "1 día", "3 días" - no se actualiza, ya está en Excel)
        - S: Vencimiento (fecha de vencimiento = Hoy + X días)
        - T: Tasa (último precio)
        - U: Monto $ (volumen)
        - V: Monto Tomador (bid_size)
        - W: Tasa Tomadora (bid)
        - X: Tasa Colocadora (ask)
        - Y: Monto Colocador (ask_size)
        
        Args:
            sheet: Objeto Sheet de xlwings
            df: DataFrame con datos de mercado
        """
        try:
            from datetime import datetime, timedelta

            # Build mapping from days to pyRofex symbols
            # Extract only caucion symbols from DataFrame
            caucion_symbols = [sym for sym in df.index if 'PESOS' in sym and 'D' in sym.split(' - ')[-1]]
            
            if not caucion_symbols:
                return  # No cauciones to update
            
            # Get today's date
            today = datetime.now().date()
            
            # Mapping from period (e.g., "3D") to row number in cauciones table
            period_to_row = {}
            for i in range(1, 61):  # Support 1-60 days
                period_to_row[f"{i}D"] = i + 1  # Row 2 is 1D, Row 3 is 2D, etc.
            period_to_row["60D"] = 34  # Special case: 60 días is at row 34
            
            # Collect updates for cauciones table
            updates = []
            
            for symbol in caucion_symbols:
                # Extract period from symbol (e.g., "MERV - XMEV - PESOS - 3D" -> "3D")
                parts = symbol.split(' - ')
                if len(parts) >= 4:
                    period = parts[3]  # e.g., "3D"
                    
                    # Get row number for this period
                    row_num = period_to_row.get(period)
                    if row_num is None:
                        continue
                    
                    # Extract number of days from period (e.g., "3D" -> 3)
                    try:
                        num_days = int(period.rstrip('D'))
                    except ValueError:
                        continue
                    
                    # Get data for this symbol
                    if symbol in df.index:
                        row_data = df.loc[symbol]
                        
                        # Calculate vencimiento (maturity date = today + num_days)
                        vencimiento = today + timedelta(days=num_days)
                        
                        # Extract values for cauciones table:
                        # Column S: Vencimiento (maturity date)
                        # Column T: Tasa (last price / 100)
                        # Column U: Monto $ (volume)
                        # Column V: Monto Tomador (bid_size)
                        # Column W: Tasa Tomadora (bid / 100)
                        # Column X: Tasa Colocadora (ask / 100)
                        # Column Y: Monto Colocador (ask_size)
                        
                        tasa_raw = get_excel_safe_value(row_data.get('last', 0))
                        tasa = tasa_raw / 100 if tasa_raw else 0
                        
                        monto = get_excel_safe_value(row_data.get('volume', 0))
                        monto_tomador = get_excel_safe_value(row_data.get('bid_size', 0))
                        
                        tasa_tomadora_raw = get_excel_safe_value(row_data.get('bid', 0))
                        tasa_tomadora = tasa_tomadora_raw / 100 if tasa_tomadora_raw else 0
                        
                        tasa_colocadora_raw = get_excel_safe_value(row_data.get('ask', 0))
                        tasa_colocadora = tasa_colocadora_raw / 100 if tasa_colocadora_raw else 0
                        
                        monto_colocador = get_excel_safe_value(row_data.get('ask_size', 0))
                        
                        # Store update: (row, [vencimiento, tasa, monto, monto_tomador, tasa_tomadora, tasa_colocadora, monto_colocador])
                        updates.append((row_num, [vencimiento, tasa, monto, monto_tomador, tasa_tomadora, tasa_colocadora, monto_colocador]))
            
            # Apply updates to Excel using BULK UPDATE for better performance
            if updates:
                # Sort by row number
                updates.sort(key=lambda x: x[0])
                
                # Find min and max row numbers
                min_row = updates[0][0]
                max_row = updates[-1][0]
                
                # Create updates dictionary for quick lookup
                updates_dict = {row_num: values for row_num, values in updates}
                
                # Build 2D array for bulk update (fill gaps with None to preserve existing data)
                bulk_data = []
                for row_idx in range(min_row, max_row + 1):
                    if row_idx in updates_dict:
                        bulk_data.append(updates_dict[row_idx])
                    else:
                        # Fill gaps with None to preserve existing Excel data
                        bulk_data.append([None] * 7)  # 7 columns: S-Y
                
                # Single bulk write for all cauciones
                range_address = f'S{min_row}:Y{max_row}'
                sheet.range(range_address).value = bulk_data
                
                logger.debug(f"✅ Actualización masiva de {len(updates)} cauciones en el rango {range_address}")
            
        except Exception as e:
            logger.error(f"Error al actualizar la tabla de cauciones: {e}")
            # Don't raise - this is a non-critical update
    
    def _update_single_instrument_row(self, sheet: xw.Sheet, symbol: str, data: pd.Series):
        """
        Actualizar una fila individual de instrumento en la hoja.
        
        Args:
            sheet: Objeto Sheet de xlwings
            symbol: Símbolo del instrumento
            data: Datos de mercado para el instrumento
        """
        try:
            # Use cached row mapping instead of searching column A every time
            if hasattr(self, '_symbol_row_cache'):
                row_index = self._symbol_row_cache.get(symbol)
            else:
                # Fallback: search column A (slower)
                symbols_range = sheet.range('A:A')
                symbols = symbols_range.value
                row_index = None
                for idx, cell_value in enumerate(symbols):
                    if cell_value == symbol:
                        row_index = idx + 1
                        break
            
            if row_index is None:
                logger.warning(f"Símbolo '{symbol}' no encontrado en la columna A de la hoja")
                return
            
            # Define column mapping (adjust based on your Excel structure)
            # Assuming: A=symbol, B=bid_size, C=bid, D=ask, E=ask_size, F=last, G=change, etc.
            column_mapping = {
                'bid_size': 'B',
                'bid': 'C',
                'ask': 'D',
                'ask_size': 'E',
                'last': 'F',
                'change': 'G',
                'open': 'H',
                'high': 'I',
                'low': 'J',
                'previous_close': 'K',
                'turnover': 'L',
                'volume': 'M',
                'operations': 'N',
                'datetime': 'O'
            }
            
            # Batch update: Prepare all values in one list for faster Excel write
            # Build row data for columns B through O (14 columns)
            row_values = []
            for field in ['bid_size', 'bid', 'ask', 'ask_size', 'last', 'change', 'open', 
                         'high', 'low', 'previous_close', 'turnover', 'volume', 'operations', 'datetime']:
                if field in data:
                    row_values.append(get_excel_safe_value(data[field]))
                else:
                    row_values.append(0)
            
            # Single batch write for entire row (B:O)
            sheet.range(f'B{row_index}:O{row_index}').value = row_values
            
            logger.info(f"✅ Actualizado {symbol} en fila {row_index} - bid={data.get('bid')}, ask={data.get('ask')}, last={data.get('last')}")
            
        except Exception as e:
            logger.warning(f"Error al actualizar fila individual para {symbol}: {e}")
    
    def clear_range(self, sheet_name: str, range_address: str) -> bool:
        """
        Limpiar datos de un rango de Excel.
        
        Args:
            sheet_name: Nombre de la hoja
            range_address: Dirección del rango de Excel a limpiar
            
        Returns:
            bool: True si fue exitoso, False en caso contrario
        """
        try:
            sheet = self.workbook.sheets(sheet_name)
            sheet.range(range_address).clear_contents()
            logger.debug(f"Rango limpiado {sheet_name}!{range_address}")
            return True
        except Exception as e:
            logger.error(f"Error al limpiar el rango {sheet_name}!{range_address}: {e}")
            return False
    
    def get_sheet_info(self, sheet_name: str) -> Dict[str, Any]:
        """
        Obtener información sobre una hoja.
        
        Args:
            sheet_name: Nombre de la hoja
            
        Returns:
            dict: Información de la hoja
        """
        try:
            sheet = self.workbook.sheets(sheet_name)
            return {
                'name': sheet.name,
                'used_range': str(sheet.used_range.address) if sheet.used_range else None,
                'visible': sheet.visible,
                'exists': True
            }
        except Exception as e:
            logger.error(f"Error al obtener información de la hoja {sheet_name}: {e}")
            return {'exists': False, 'error': str(e)}
    
    def format_range(self, sheet_name: str, range_address: str, 
                     format_dict: Dict[str, Any]) -> bool:
        """
        Aplicar formato a un rango de Excel.
        
        Args:
            sheet_name: Nombre de la hoja
            range_address: Dirección del rango de Excel
            format_dict: Diccionario con opciones de formato
            
        Returns:
            bool: True si fue exitoso, False en caso contrario
        """
        try:
            sheet = self.workbook.sheets(sheet_name)
            range_obj = sheet.range(range_address)
            
            # Apply formatting based on format_dict
            for format_key, format_value in format_dict.items():
                if format_key == 'number_format':
                    range_obj.number_format = format_value
                elif format_key == 'font_bold':
                    range_obj.font.bold = format_value
                elif format_key == 'font_size':
                    range_obj.font.size = format_value
                elif format_key == 'background_color':
                    range_obj.color = format_value
                # Add more formatting options as needed
            
            logger.debug(f"Formato aplicado a {sheet_name}!{range_address}")
            return True
            
        except Exception as e:
            logger.error(f"Error al aplicar formato al rango {sheet_name}!{range_address}: {e}")
            return False
    
    def copy_range(self, source_sheet: str, source_range: str,
                   dest_sheet: str, dest_range: str) -> bool:
        """
        Copiar datos de un rango a otro.
        
        Args:
            source_sheet: Nombre de la hoja origen
            source_range: Dirección del rango origen
            dest_sheet: Nombre de la hoja destino
            dest_range: Dirección del rango destino
            
        Returns:
            bool: True si fue exitoso, False en caso contrario
        """
        try:
            # Get source data
            source_data = self.read_range(source_sheet, source_range)
            if source_data is None:
                return False
            
            # Write to destination
            return self.write_range(dest_sheet, dest_range, source_data)
            
        except Exception as e:
            logger.error(f"Error al copiar rango: {e}")
            return False
    
    def get_update_stats(self) -> Dict[str, Any]:
        """
        Obtener estadísticas de actualización.
        
        Returns:
            dict: Estadísticas de actualización
        """
        return self.update_stats.copy()
    
    def reset_stats(self):
        """Reiniciar estadísticas de actualización."""
        self.update_stats = {
            'updates_performed': 0,
            'errors': 0,
            'last_update_time': None
        }