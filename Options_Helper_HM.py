import pandas as pd
from datetime import date, timedelta
from dateutil.relativedelta import relativedelta
import datetime
import xlwings as xw

# Importante: Verificar que el nombre coincida exactamente con nuestro archivo de Excel. De lo contrario, modificarlo
wb = xw.Book('EPGB OC-DI - Python.xlsb')
shtTickers = wb.sheets('Tickers')
allOptions = pd.DataFrame()
oOpciones = pd.DataFrame()


# Symbol transformation function for pyRofex integration
def transform_symbol_for_pyrofex(raw_symbol):
    """
    Transform symbols for pyRofex compatibility:
    - Add "MERV - XMEV - " prefix to all symbols
    - Replace " - spot" suffix with " - CI"
    - Preserve other suffixes (" - 24hs", etc.)
    
    Examples:
    - "YPFD - 24hs" → "MERV - XMEV - YPFD - 24hs"
    - "GGAL - spot" → "MERV - XMEV - GGAL - CI"
    - "BBAR - CI" → "MERV - XMEV - BBAR - CI"
    """
    if not raw_symbol or not isinstance(raw_symbol, str):
        return raw_symbol
    
    # Add MERV - XMEV - prefix
    transformed = "MERV - XMEV - " + raw_symbol
    
    # Replace " - spot" suffix with " - CI"
    if transformed.endswith(" - spot"):
        transformed = transformed.replace(" - spot", " - CI")
    
    return transformed


# Aca definimos el rango de datos que vamos a cargar en el Excel, en la hoja "Tickers". En este caso, le deje un rango desde la fila 2 a la 500.
# En caso de superar la fila 500 en el excel para algun grupo, modificarlo en esta linea:   rng = shtTickers.range('Columna2:Columna500')

#Grupo Opciones: Excel Hoja Tickers: Columna A, filas 2 a 500

def getOptionsList():
    global allOptions
    rng = shtTickers.range('A2:A500').expand()
    oOpciones = rng.value
    
    # Apply pyRofex symbol transformation to all symbols
    if isinstance(oOpciones, list):
        oOpciones = [transform_symbol_for_pyrofex(symbol) for symbol in oOpciones if symbol is not None]
    elif oOpciones is not None:
        oOpciones = [transform_symbol_for_pyrofex(oOpciones)]
    else:
        oOpciones = []
    
    allOptions = pd.DataFrame({'symbol': oOpciones},
                              columns=["symbol", "bid_size", "bid", "ask", "ask_size", "last",
                                       "change", "open", "high", "low", "previous_close", "turnover", "volume",
                                       'operations', 'datetime'])
    allOptions = allOptions.set_index('symbol')
    allOptions['datetime'] = pd.to_datetime(allOptions['datetime'])

    return allOptions


#Grupo Acciones: Excel Hoja Tickers: Columna C, filas 2 a 500

def getAccionesList():
    rng = shtTickers.range('C2:C500').expand()
    oAcciones = rng.value
    
    # Apply pyRofex symbol transformation to all symbols
    if isinstance(oAcciones, list):
        oAcciones = [transform_symbol_for_pyrofex(symbol) for symbol in oAcciones if symbol is not None]
    elif oAcciones is not None:
        oAcciones = [transform_symbol_for_pyrofex(oAcciones)]
    else:
        oAcciones = []
    
    ACC = pd.DataFrame({'symbol' : oAcciones}, columns=["symbol", "bid_size", "bid", "ask", "ask_size", "last",
                                                                             "change", "open", "high", "low", "previous_close", "turnover", "volume",
                                                                             'operations', 'datetime'])
    ACC = ACC.set_index('symbol')
    ACC['datetime'] = pd.to_datetime(ACC['datetime'])
    return ACC

#Grupo Bonos: Excel Hoja Tickers: Columna E, filas 2 a 500

def getBonosList():
    rng = shtTickers.range('E2:E500').expand()
    oBonos = rng.value
    
    # Apply pyRofex symbol transformation to all symbols
    if isinstance(oBonos, list):
        oBonos = [transform_symbol_for_pyrofex(symbol) for symbol in oBonos if symbol is not None]
    elif oBonos is not None:
        oBonos = [transform_symbol_for_pyrofex(oBonos)]
    else:
        oBonos = []
    
    Bonos = pd.DataFrame({'symbol' : oBonos}, columns=["symbol", "bid_size", "bid", "ask", "ask_size", "last",
                                                                             "change", "open", "high", "low", "previous_close", "turnover", "volume",
                                                                             'operations', 'datetime'])
    Bonos = Bonos.set_index('symbol')
    Bonos['datetime'] = pd.to_datetime(Bonos['datetime'])
    return Bonos

#Grupo CEDEARS: Excel Hoja Tickers: Columna G, filas 2 a 500

def getCedearsList():
    rng = shtTickers.range('G2:G500').expand()
    oCedears = rng.value
    
    # Apply pyRofex symbol transformation to all symbols
    if isinstance(oCedears, list):
        oCedears = [transform_symbol_for_pyrofex(symbol) for symbol in oCedears if symbol is not None]
    elif oCedears is not None:
        oCedears = [transform_symbol_for_pyrofex(oCedears)]
    else:
        oCedears = []
    
    Cedears = pd.DataFrame({'symbol' : oCedears}, columns=["symbol", "bid_size", "bid", "ask", "ask_size", "last",
                                                                             "change", "open", "high", "low", "previous_close", "turnover", "volume",
                                                                             'operations', 'datetime'])
    Cedears = Cedears.set_index('symbol')
    Cedears['datetime'] = pd.to_datetime(Cedears['datetime'])
    return Cedears


#Grupo Letras: Excel Hoja Tickers: Columna I, filas 2 a 500

def getLetrasList():
    rng = shtTickers.range('I2:I500').expand()
    oLetras = rng.value
    
    # Apply pyRofex symbol transformation to all symbols
    if isinstance(oLetras, list):
        oLetras = [transform_symbol_for_pyrofex(symbol) for symbol in oLetras if symbol is not None]
    elif oLetras is not None:
        oLetras = [transform_symbol_for_pyrofex(oLetras)]
    else:
        oLetras = []
     
    Letras = pd.DataFrame({'symbol' : oLetras}, columns=["symbol", "bid_size", "bid", "ask", "ask_size", "last",
                                                                            "change", "open", "high", "low", "previous_close", "turnover", "volume",
                                                                            'operations', 'datetime'])
    Letras = Letras.set_index('symbol')
    Letras['datetime'] = pd.to_datetime(Letras['datetime'])
    return Letras


#Grupo ONS: Excel Hoja Tickers: Columna K, filas 2 a 500

def getONSList():
    rng = shtTickers.range('K2:K500').expand()
    oONS = rng.value
    
    # Apply pyRofex symbol transformation to all symbols
    if isinstance(oONS, list):
        oONS = [transform_symbol_for_pyrofex(symbol) for symbol in oONS if symbol is not None]
    elif oONS is not None:
        oONS = [transform_symbol_for_pyrofex(oONS)]
    else:
        oONS = []
     
    ONS = pd.DataFrame({'symbol' : oONS}, columns=["symbol", "bid_size", "bid", "ask", "ask_size", "last",
                                                                             "change", "open", "high", "low", "previous_close", "turnover", "volume",
                                                                             'operations', 'datetime'])
    ONS = ONS.set_index('symbol')
    ONS['datetime'] = pd.to_datetime(ONS['datetime'])
    return ONS


#Grupo Acciones del Panel General: Excel Hoja Tickers: Columna M, filas 2 a 500

def getPanelGeneralList():
    rng = shtTickers.range('M2:M500').expand()
    oPanelGeneral = rng.value
    
    # Apply pyRofex symbol transformation to all symbols
    if isinstance(oPanelGeneral, list):
        oPanelGeneral = [transform_symbol_for_pyrofex(symbol) for symbol in oPanelGeneral if symbol is not None]
    elif oPanelGeneral is not None:
        oPanelGeneral = [transform_symbol_for_pyrofex(oPanelGeneral)]
    else:
        oPanelGeneral = []
     
    PanelGeneral = pd.DataFrame({'symbol' : oPanelGeneral}, columns=["symbol", "bid_size", "bid", "ask", "ask_size", "last",
                                                                            "change", "open", "high", "low", "previous_close", "turnover", "volume",
                                                                            'operations', 'datetime'])
    PanelGeneral = PanelGeneral.set_index('symbol')
    PanelGeneral['datetime'] = pd.to_datetime(PanelGeneral['datetime'])
    return PanelGeneral


# Cauciones
i = 1
fechas = []
while i < 31:
    fecha = date.today() + timedelta(days=i)
    fechas.extend([fecha])
    i += 1

cauciones = pd.DataFrame({'settlement':fechas}, columns=['settlement','last', 'turnover', 'bid_amount', 'bid_rate', 'ask_rate', 'ask_amount'])
cauciones['settlement'] = pd.to_datetime(cauciones['settlement'])
cauciones = cauciones.set_index('settlement')


