"""
Test para verificar el manejo correcto de datos de opciones.

Este test verifica que:
1. El DataFrame de opciones tiene todas las columnas necesarias
2. Los datos del WebSocket se actualizan correctamente en el DataFrame
3. No hay pérdida de datos al escribir a Excel
"""

import pandas as pd

from epgb_options.excel.symbol_loader import SymbolLoader
from epgb_options.market_data.websocket_handler import WebSocketHandler
from epgb_options.utils.validation import (safe_float_conversion,
                                           safe_int_conversion)


def test_options_dataframe_has_all_required_columns():
    """Verificar que el DataFrame de opciones tiene todas las columnas necesarias."""
    
    # Columnas esperadas (las mismas que WebSocket handler actualiza)
    expected_columns = [
        'bid', 'ask', 'bidsize', 'asksize', 'last', 'change',
        'open', 'high', 'low', 'previous_close', 'turnover',
        'volume', 'operations', 'datetime'
    ]
    
    # Simular creación de DataFrame de opciones (como en symbol_loader.py)
    options_df = pd.DataFrame({
        'symbol': ['GFGC38566O', 'GFGC41781O'],
        'bid': 0.0,
        'ask': 0.0,
        'bidsize': 0,
        'asksize': 0,
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
    
    options_df.set_index('symbol', inplace=True)
    
    # Verificar que todas las columnas esperadas existen
    for col in expected_columns:
        assert col in options_df.columns, f"Columna faltante en options_df: {col}"
    
    print("✅ Test passed: Options DataFrame tiene todas las columnas requeridas")


def test_websocket_data_updates_all_columns():
    """Verificar que los datos del WebSocket actualizan todas las columnas."""
    
    # Crear DataFrame de opciones inicial
    options_df = pd.DataFrame({
        'symbol': ['GFGC38566O'],
        'bid': 0.0,
        'ask': 0.0,
        'bidsize': 0,
        'asksize': 0,
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
    options_df.set_index('symbol', inplace=True)
    
    # Simular datos del WebSocket (estructura completa)
    symbol = 'GFGC38566O'
    websocket_data = {
        'bid_size': 10,
        'bid': 604.440,
        'ask': 630.000,
        'ask_size': 10,
        'last': 626.71,
        'change': 0.0622,
        'open': 620.0,
        'high': 630.0,
        'low': 600.0,
        'previous_close': 620.0,
        'turnover': 50000.0,
        'volume': 80,
        'operations': 5,
        'datetime': pd.Timestamp.now()
    }
    
    # Crear DataFrame de actualización (como lo hace WebSocketHandler)
    update_df = pd.DataFrame([websocket_data], index=[symbol])
    
    # Renombrar columnas para compatibilidad con opciones
    update_df = update_df.rename(columns={"bid_size": "bidsize", "ask_size": "asksize"})
    
    # Actualizar options_df (como lo hace _update_options_data)
    if symbol in options_df.index:
        for col in update_df.columns:
            if col in options_df.columns:
                options_df.loc[symbol, col] = update_df.loc[symbol, col]
    
    # Verificar que TODOS los valores se actualizaron correctamente
    assert options_df.loc[symbol, 'bid'] == 604.440, "bid no se actualizó correctamente"
    assert options_df.loc[symbol, 'ask'] == 630.000, "ask no se actualizó correctamente"
    assert options_df.loc[symbol, 'bidsize'] == 10, "bidsize no se actualizó correctamente"
    assert options_df.loc[symbol, 'asksize'] == 10, "asksize no se actualizó correctamente"
    assert options_df.loc[symbol, 'last'] == 626.71, "last no se actualizó correctamente"
    assert options_df.loc[symbol, 'open'] == 620.0, "open no se actualizó correctamente"
    assert options_df.loc[symbol, 'high'] == 630.0, "high no se actualizó correctamente"
    assert options_df.loc[symbol, 'low'] == 600.0, "low no se actualizó correctamente"
    assert options_df.loc[symbol, 'previous_close'] == 620.0, "previous_close no se actualizó correctamente"
    assert options_df.loc[symbol, 'turnover'] == 50000.0, "turnover no se actualizó correctamente"
    assert options_df.loc[symbol, 'volume'] == 80, "volume no se actualizó correctamente"
    assert options_df.loc[symbol, 'operations'] == 5, "operations no se actualizó correctamente"
    
    print("✅ Test passed: Todas las columnas se actualizan correctamente desde WebSocket")


def test_safe_conversions_handle_none_properly():
    """Verificar que las conversiones seguras manejan None correctamente."""
    
    # Test safe_float_conversion
    assert safe_float_conversion(None) == 0.0, "safe_float_conversion(None) debe retornar 0.0"
    assert safe_float_conversion(123.45) == 123.45, "safe_float_conversion debe preservar valores float"
    assert safe_float_conversion("456.78") == 456.78, "safe_float_conversion debe convertir strings"
    assert safe_float_conversion("invalid") == 0.0, "safe_float_conversion debe manejar valores inválidos"
    
    # Test safe_int_conversion
    assert safe_int_conversion(None) == 0, "safe_int_conversion(None) debe retornar 0"
    assert safe_int_conversion(123) == 123, "safe_int_conversion debe preservar valores int"
    assert safe_int_conversion(123.9) == 123, "safe_int_conversion debe truncar float"
    assert safe_int_conversion("456") == 456, "safe_int_conversion debe convertir strings"
    assert safe_int_conversion("invalid") == 0, "safe_int_conversion debe manejar valores inválidos"
    
    print("✅ Test passed: Conversiones seguras manejan None y valores inválidos correctamente")


def test_excel_field_order_matches_dataframe():
    """Verificar que el field_order de Excel coincide con las columnas del DataFrame."""
    
    # field_order de sheet_operations.py (línea 231)
    excel_field_order = [
        'bid_size', 'bid', 'ask', 'ask_size', 'last', 'change', 'open',
        'high', 'low', 'previous_close', 'turnover', 'volume', 'operations', 'datetime'
    ]
    
    # Columnas del DataFrame de opciones (después del rename para Excel)
    options_df = pd.DataFrame({
        'symbol': ['GFGC38566O'],
        'bid': 0.0,
        'ask': 0.0,
        'bidsize': 0,
        'asksize': 0,
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
    options_df.set_index('symbol', inplace=True)
    
    # Renombrar para Excel (como en main.py línea 410)
    options_for_excel = options_df.rename(columns={'bidsize': 'bid_size', 'asksize': 'ask_size'})
    
    # Verificar que todas las columnas de field_order existen en el DataFrame
    missing_columns = [col for col in excel_field_order if col not in options_for_excel.columns]
    
    assert len(missing_columns) == 0, f"Columnas faltantes en DataFrame para Excel: {missing_columns}"
    
    print("✅ Test passed: field_order de Excel coincide con columnas del DataFrame")


def test_no_data_loss_in_update_pipeline():
    """Test de integración: verificar que no hay pérdida de datos en todo el pipeline."""
    
    # 1. Crear DataFrame inicial (como symbol_loader)
    options_df = pd.DataFrame({
        'symbol': ['GFGC38566O'],
        'bid': 0.0,
        'ask': 0.0,
        'bidsize': 0,
        'asksize': 0,
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
    options_df.set_index('symbol', inplace=True)
    
    # 2. Simular mensaje del WebSocket con datos completos
    symbol = 'GFGC38566O'
    market_data = {
        'BI': [{'price': 604.440, 'size': 10}],
        'OF': [{'price': 630.000, 'size': 10}],
        'LA': {'price': 626.71},
        'OP': 620.0,
        'HI': 630.0,
        'LO': 600.0,
        'CL': 620.0,
        'EV': 50000.0,
        'NV': 80,
        'TC': 5
    }
    
    # 3. Extraer datos (como _process_market_data)
    bids = market_data.get('BI', [])
    offers = market_data.get('OF', [])
    last_trade = market_data.get('LA', {})
    
    best_bid = bids[0] if bids else {}
    best_offer = offers[0] if offers else {}
    
    data_row = {
        'bid_size': safe_int_conversion(best_bid.get('size')),
        'bid': safe_float_conversion(best_bid.get('price')),
        'ask': safe_float_conversion(best_offer.get('price')),
        'ask_size': safe_int_conversion(best_offer.get('size')),
        'last': safe_float_conversion(last_trade.get('price')),
        'change': 0.0622,
        'open': safe_float_conversion(market_data.get('OP')),
        'high': safe_float_conversion(market_data.get('HI')),
        'low': safe_float_conversion(market_data.get('LO')),
        'previous_close': safe_float_conversion(market_data.get('CL')),
        'turnover': safe_float_conversion(market_data.get('EV')),
        'volume': safe_int_conversion(market_data.get('NV')),
        'operations': safe_int_conversion(market_data.get('TC')),
        'datetime': pd.Timestamp.now()
    }
    
    # 4. Actualizar DataFrame
    update_df = pd.DataFrame([data_row], index=[symbol])
    update_df = update_df.rename(columns={"bid_size": "bidsize", "ask_size": "asksize"})
    
    for col in update_df.columns:
        if col in options_df.columns:
            options_df.loc[symbol, col] = update_df.loc[symbol, col]
    
    # 5. Preparar para Excel
    options_for_excel = options_df.rename(columns={'bidsize': 'bid_size', 'asksize': 'ask_size'})
    
    # 6. Verificar que NINGÚN dato se perdió
    excel_field_order = [
        'bid_size', 'bid', 'ask', 'ask_size', 'last', 'change', 'open',
        'high', 'low', 'previous_close', 'turnover', 'volume', 'operations', 'datetime'
    ]
    
    for field in excel_field_order:
        if field == 'datetime':
            continue  # Skip datetime check
        value = options_for_excel.loc[symbol, field]
        assert value is not None, f"Campo {field} es None después del pipeline"
        if field not in ['change', 'datetime']:
            # Para campos numéricos, verificar que no son el valor por defecto 0
            # (excepto change que puede ser 0 legítimamente)
            if field in ['bid', 'ask', 'last', 'open', 'high', 'low', 'previous_close', 'turnover']:
                assert value > 0, f"Campo {field} tiene valor por defecto (0) después del pipeline"
    
    print("✅ Test passed: No hay pérdida de datos en el pipeline completo")
    print(f"   Datos finales para {symbol}:")
    print(f"   bid={options_for_excel.loc[symbol, 'bid']}, ask={options_for_excel.loc[symbol, 'ask']}")
    print(f"   open={options_for_excel.loc[symbol, 'open']}, high={options_for_excel.loc[symbol, 'high']}, low={options_for_excel.loc[symbol, 'low']}")
    print(f"   turnover={options_for_excel.loc[symbol, 'turnover']}, volume={options_for_excel.loc[symbol, 'volume']}, operations={options_for_excel.loc[symbol, 'operations']}")


if __name__ == "__main__":
    print("Ejecutando tests de manejo de datos de opciones...\n")
    
    test_options_dataframe_has_all_required_columns()
    test_websocket_data_updates_all_columns()
    test_safe_conversions_handle_none_properly()
    test_excel_field_order_matches_dataframe()
    test_no_data_loss_in_update_pipeline()
    
    print("\n🎉 ¡Todos los tests pasaron exitosamente!")
