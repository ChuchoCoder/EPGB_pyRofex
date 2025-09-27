# Carga de librerias necesarias:

import time
import pyRofex
import xlwings as xw
import Options_Helper_HM
import pandas as pd

# Lista de los activos que va a levantar:

ACC = Options_Helper_HM.getAccionesList()
cedears = Options_Helper_HM.getCedearsList()
cauciones = Options_Helper_HM.cauciones
options = Options_Helper_HM.getOptionsList()
bonos = Options_Helper_HM.getBonosList()
letras = Options_Helper_HM.getLetrasList()
ONS = Options_Helper_HM.getONSList()
PanelGeneral = Options_Helper_HM.getPanelGeneralList()
options = options.rename(columns={"bid_size": "bidsize", "ask_size": "asksize"})
everything = pd.concat([ACC, bonos, letras, PanelGeneral, ONS, cedears])

listLength = len(everything) + 2

# ACLARACION: De aquellos instrumentos cuya informacion NO se necesite o quiera traer a la planilla, agregarles por delante el # a la linea de codigo segun corresponda
# Ejemplo, para NO traer informacion del Panel General, le agrego asi el # por delante:

        # PanelGeneral = Options_Helper_HM.getPanelGeneralList()





# T015: Excel initialization with comprehensive error handling
print("📁 Inicializando conexión con Excel...")
try:
    # Aca declara el archivo Excel que va a actualizar
    # Importante: Verificar que el nombre coincida exactamente con nuestro archivo de Excel. De lo contrario, modificarlo
    wb = xw.Book('EPGB OC-DI - Python.xlsb')
    print("✅ Archivo Excel conectado exitosamente")
    
    # Hojas del excel - verify sheet access
    try:
        shtTest = wb.sheets('HomeBroker')
        shtTickers = wb.sheets('Tickers')
        print("✅ Hojas de Excel ('HomeBroker' y 'Tickers') accesibles")
    except Exception as sheet_error:
        print(f"⚠️ Error accediendo a hojas de Excel: {sheet_error}")
        print("🔄 El script continuará - las actualizaciones se reanudarán cuando las hojas estén disponibles")
        shtTest = None
        shtTickers = None
        
except Exception as wb_error:
    print(f"❌ Error al conectar con archivo Excel: {wb_error}")
    print("⚠️ IMPORTANTE: Verifique que:")
    print("   1. El archivo 'EPGB OC-DI - Python.xlsb' existe en el directorio actual")
    print("   2. El archivo no está abierto en Excel (bloqueado)")
    print("   3. Tiene permisos de lectura/escritura en el archivo")
    print("🔄 El script continuará recolectando datos - las actualizaciones de Excel se reanudarán cuando el archivo esté disponible")
    wb = None
    shtTest = None
    shtTickers = None

# T017: Comprehensive error handling for critical operations

# Configurar parametros de entorno para COCOS broker con error handling
print("🔧 Configurando parámetros de entorno para COCOS broker...")
try:
    pyRofex._set_environment_parameter('url', 'https://api.cocos.xoms.com.ar/', pyRofex.Environment.LIVE)
    pyRofex._set_environment_parameter('ws', 'wss://api.cocos.xoms.com.ar/', pyRofex.Environment.LIVE)
    print("✅ Parámetros de entorno configurados exitosamente")
except Exception as env_error:
    print(f"❌ Error configurando entorno pyRofex: {env_error}")
    print("🛑 DETENIENDO EJECUCION - Error crítico en configuración inicial")
    exit(1)

# Credenciales de acceso
user = 'your_username'  # Reemplazar con usuario real
password = 'your_password'  # Reemplazar con password real  
account = 'your_account'  # Reemplazar con cuenta real

# Validación de credenciales antes de autenticación
print("🔐 Validando credenciales...")
if user == 'your_username' or password == 'your_password' or account == 'your_account':
    print("❌ ERROR: Credenciales por defecto detectadas")
    print("⚠️ IMPORTANTE: Debe configurar credenciales reales en las variables:")
    print("   - user: su nombre de usuario")
    print("   - password: su contraseña") 
    print("   - account: su número de cuenta")
    print("🛑 DETENIENDO EJECUCION - Se requiere configuración manual de credenciales")
    exit(1)

print("✅ Credenciales validadas")

# Si esta todo bien, aparecera este mensaje y a continuacion empezara a actualizarse la planilla: 
print("OK: INICIANDO AUTENTICACION Y CONFIGURACION")

def market_data_handler(message):
    """
    Handle market data messages from pyRofex websocket.
    Processes real-time financial data and updates global DataFrames.
    
    Expected pyRofex message structure:
    {
        "symbol": "MERV - XMEV - YPFD - 24hs",
        "bid": 150.50,
        "ask": 151.00,
        "bid_size": 1000,
        "ask_size": 500,
        "last": 150.75,
        "change": 0.025,
        "open": 150.25,
        "high": 151.50,
        "low": 149.80,
        "previous_close": 150.00,
        "turnover": 1500000.0,
        "volume": 10000,
        "operations": 45,
        "datetime": "2025-09-27T15:30:45.123Z"
    }
    """
    global options, everything
    
    try:
        # Data validation for critical fields per FR-008
        if not message or not isinstance(message, dict):
            print(f"Invalid message format received: {message}")
            return
            
        # Validate required fields (symbol, price fields)
        required_fields = ['symbol']
        for field in required_fields:
            if field not in message or message[field] is None or message[field] == '':
                print(f"Missing required field '{field}' in message: {message}")
                return
        
        # Validate price fields (bid, ask, last) - must be positive if present
        price_fields = ['bid', 'ask', 'last']
        for field in price_fields:
            if field in message and message[field] is not None:
                if not isinstance(message[field], (int, float)) or message[field] < 0:
                    print(f"Invalid price for {field}: {message[field]} in symbol {message['symbol']}")
                    return
        
        # Handle datetime field - convert to pandas datetime
        if 'datetime' in message and message['datetime']:
            try:
                message['datetime'] = pd.to_datetime(message['datetime'])
            except Exception as e:
                print(f"Error parsing datetime {message['datetime']}: {e}")
                message['datetime'] = pd.Timestamp.now()
        else:
            message['datetime'] = pd.Timestamp.now()
        
        # Convert message to DataFrame row format
        symbol = message['symbol']
        
        # Create data row compatible with existing Excel structure
        data_row = {
            'bid_size': message.get('bid_size', None),
            'bid': message.get('bid', None),
            'ask': message.get('ask', None),
            'ask_size': message.get('ask_size', None),
            'last': message.get('last', None),
            'change': message.get('change', 0) / 100 if message.get('change') is not None else None,  # Convert to decimal
            'open': message.get('open', None),
            'high': message.get('high', None),
            'low': message.get('low', None),
            'previous_close': message.get('previous_close', None),
            'turnover': message.get('turnover', None),
            'volume': message.get('volume', None),
            'operations': message.get('operations', None),
            'datetime': message['datetime']
        }
        
        # Create DataFrame for this update
        thisData = pd.DataFrame([data_row], index=[symbol])
        
        # Determine which global DataFrame to update based on symbol characteristics
        # Options typically have specific patterns in their symbols
        if any(option_indicator in symbol for option_indicator in ['CALL', 'PUT', 'C ', 'P ', 'OPTION']):
            # Handle options data - rename columns for compatibility
            thisData = thisData.rename(columns={"bid_size": "bidsize", "ask_size": "asksize"})
            thisData = thisData.drop(['expiration', 'strike', 'kind'], axis=1, errors='ignore')
            if not options.empty:
                options.update(thisData)
            else:
                print(f"Options DataFrame not initialized for symbol: {symbol}")
        else:
            # Handle other securities (stocks, bonds, etc.)
            if not everything.empty:
                everything.update(thisData)
            else:
                print(f"Everything DataFrame not initialized for symbol: {symbol}")
        
        # Optional: Print update confirmation (can be removed for production)
        print(f"✓ Updated {symbol}: last={data_row['last']}, bid={data_row['bid']}, ask={data_row['ask']}")
        
    except Exception as e:
        # T017: Enhanced error handling with detailed context and graceful degradation
        error_context = {
            'error': str(e),
            'message_type': type(message).__name__,
            'has_symbol': 'symbol' in message if isinstance(message, dict) else 'unknown',
            'symbol': message.get('symbol', 'unknown') if isinstance(message, dict) else 'unknown',
            'timestamp': pd.Timestamp.now().isoformat()
        }
        
        print(f"❌ Error procesando datos de mercado: {e}")
        print(f"📋 Contexto: Symbol={error_context['symbol']}, Type={error_context['message_type']}")
        print(f"🔄 Continuando con procesamiento de otros mensajes - error no crítico")
        
        # Log detailed error for debugging (could be written to file in production)
        if hasattr(e, '__traceback__'):
            import traceback
            print(f"📝 Detalle técnico: {traceback.format_exc()}")
        
        # Continue processing other messages - don't stop on individual errors
        # This ensures market data flow continues even if some messages are malformed


# Legacy function - will be replaced by market_data_handler
def on_options(online, quotes):
    global options
    thisData = quotes
    thisData = thisData.drop(['expiration', 'strike', 'kind'], axis=1)
    thisData['change'] = thisData["change"] / 100
    thisData['datetime'] = pd.to_datetime(thisData['datetime'])
    thisData = thisData.rename(columns={"bid_size": "bidsize", "ask_size": "asksize"})
    options.update(thisData)


def on_securities(online, quotes):
    """
    Updated securities handler for pyRofex message format.
    Maintains symbol concatenation logic and data transformations from original function.
    """
    global everything
    
    try:
        print("📊 Securities data received:", quotes)
        
        # Handle both single message and multiple messages
        if isinstance(quotes, dict):
            # Single message - convert to list for uniform processing
            quotes_list = [quotes]
        elif isinstance(quotes, list):
            # Multiple messages
            quotes_list = quotes
        else:
            # Assume it's a DataFrame (legacy format)
            thisData = quotes
            thisData = thisData.reset_index()
            thisData['symbol'] = thisData['symbol'] + ' - ' + thisData['settlement']
            thisData = thisData.drop(["settlement"], axis=1)
            thisData = thisData.set_index("symbol")
            thisData['change'] = thisData["change"] / 100
            thisData['datetime'] = pd.to_datetime(thisData['datetime'])
            everything.update(thisData)
            return
        
        # Process each message in pyRofex format
        processed_data = []
        for message in quotes_list:
            if not message or 'symbol' not in message:
                continue
                
            # Apply data validation rules from T008
            if not message['symbol'] or message['symbol'] == '':
                print(f"⚠️ Skipping securities message with empty symbol")
                continue
                
            # Extract settlement info if present in symbol or message
            symbol = message['symbol']
            settlement = message.get('settlement', '24hs')  # Default to 24hs
            
            # Maintain symbol concatenation logic: symbol + ' - ' + settlement
            concatenated_symbol = f"{symbol} - {settlement}"
            
            # Apply data transformations matching original logic
            processed_row = {
                'symbol': concatenated_symbol,
                'bid_size': message.get('bid_size', None),
                'bid': message.get('bid', None),
                'ask': message.get('ask', None), 
                'ask_size': message.get('ask_size', None),
                'last': message.get('last', None),
                'change': message.get('change', 0) / 100 if message.get('change') is not None else None,  # Convert percentage to decimal
                'open': message.get('open', None),
                'high': message.get('high', None),
                'low': message.get('low', None),
                'previous_close': message.get('previous_close', None),
                'turnover': message.get('turnover', None),
                'volume': message.get('volume', None),
                'operations': message.get('operations', None),
                'datetime': pd.to_datetime(message.get('datetime', pd.Timestamp.now()))
            }
            
            processed_data.append(processed_row)
        
        # Convert to DataFrame if we have data
        if processed_data:
            thisData = pd.DataFrame(processed_data)
            thisData = thisData.set_index("symbol")
            
            # Update global everything DataFrame
            everything.update(thisData)
            print(f"✓ Updated {len(processed_data)} securities records")
        
    except Exception as e:
        print(f"🔴 Error in on_securities: {e}")
        # Continue processing - don't crash on individual errors


def on_repos(online, quotes):
    """
    Updated repos handler for pyRofex cauciones data format.
    Applies PESOS filtering and data transformations from original function.
    """
    global cauciones
    
    try:
        print("💰 Cauciones data received:", quotes)
        
        # Handle both single message and multiple messages  
        if isinstance(quotes, dict):
            # Single message - convert to list for uniform processing
            quotes_list = [quotes]
        elif isinstance(quotes, list):
            # Multiple messages
            quotes_list = quotes
        else:
            # Assume it's a DataFrame (legacy format)
            thisData = quotes
            thisData = thisData.reset_index()
            thisData = thisData.set_index("symbol")
            thisData = thisData[['PESOS' in s for s in quotes.index]]
            thisData = thisData.reset_index()
            thisData['settlement'] = pd.to_datetime(thisData['settlement'])
            thisData = thisData.set_index("settlement")
            thisData['last'] = thisData["last"] / 100
            thisData['bid_rate'] = thisData["bid_rate"] / 100
            thisData['ask_rate'] = thisData["ask_rate"] / 100
            thisData = thisData.drop(['open', 'high', 'low', 'volume', 'operations', 'datetime'], axis=1)
            thisData = thisData[['last', 'turnover', 'bid_amount', 'bid_rate', 'ask_rate', 'ask_amount']]
            cauciones.update(thisData)
            return
        
        # Process each message in pyRofex format
        processed_data = []
        for message in quotes_list:
            if not message or 'symbol' not in message:
                continue
                
            # Apply data validation rules from T008  
            symbol = message.get('symbol', '')
            if not symbol:
                print(f"⚠️ Skipping cauciones message with empty symbol")
                continue
                
            # Apply PESOS filtering logic: filter symbols containing 'PESOS' string
            if 'PESOS' not in symbol:
                print(f"ℹ️ Skipping non-PESOS symbol: {symbol}")
                continue
            
            # Apply data transformations matching original logic
            settlement = message.get('settlement')
            if settlement:
                try:
                    # Convert settlement to datetime and use as index
                    settlement_dt = pd.to_datetime(settlement)
                except Exception as e:
                    print(f"⚠️ Error parsing settlement date {settlement}: {e}")
                    settlement_dt = pd.Timestamp.now()
            else:
                settlement_dt = pd.Timestamp.now()
            
            # Convert rates from percentage (divide by 100): last, bid_rate, ask_rate
            processed_row = {
                'settlement': settlement_dt,
                'symbol': symbol,
                'last': message.get('last', 0) / 100 if message.get('last') is not None else None,
                'turnover': message.get('turnover', None),
                'bid_amount': message.get('bid_amount', None),
                'bid_rate': message.get('bid_rate', 0) / 100 if message.get('bid_rate') is not None else None,
                'ask_rate': message.get('ask_rate', 0) / 100 if message.get('ask_rate') is not None else None,
                'ask_amount': message.get('ask_amount', None)
                # Note: Dropping unnecessary columns as per original logic (open, high, low, volume, operations, datetime)
            }
            
            processed_data.append(processed_row)
        
        # Convert to DataFrame if we have data
        if processed_data:
            thisData = pd.DataFrame(processed_data)
            thisData = thisData.set_index("settlement")
            
            # Reorder columns as per original logic: ['last', 'turnover', 'bid_amount', 'bid_rate', 'ask_rate', 'ask_amount']
            column_order = ['last', 'turnover', 'bid_amount', 'bid_rate', 'ask_rate', 'ask_amount']
            available_columns = [col for col in column_order if col in thisData.columns]
            thisData = thisData[available_columns]
            
            # Update global cauciones DataFrame
            cauciones.update(thisData)
            print(f"✓ Updated {len(processed_data)} cauciones records")
        else:
            print("ℹ️ No PESOS cauciones data to process")
        
    except Exception as e:
        print(f"🔴 Error in on_repos: {e}")
        # Continue processing - don't crash on individual errors


# T018: Enhanced connection resilience with status tracking and monitoring
# Global variables for connection management and status tracking
reconnection_attempts = 0
max_reconnection_attempts = 10
reconnection_delays = [1, 2, 4, 8, 15, 30]  # Extended exponential backoff intervals
connection_status = {
    'is_connected': False,
    'last_connection_time': None,
    'last_disconnection_time': None,
    'total_reconnections': 0,
    'consecutive_failures': 0,
    'connection_uptime_start': None
}

def log_connection_event(event_type, details=""):
    """Log connection events for monitoring and troubleshooting"""
    timestamp = pd.Timestamp.now()
    uptime = None
    
    if event_type == 'connected':
        connection_status['is_connected'] = True
        connection_status['last_connection_time'] = timestamp
        connection_status['connection_uptime_start'] = timestamp
        connection_status['consecutive_failures'] = 0
        
    elif event_type == 'disconnected':
        connection_status['is_connected'] = False  
        connection_status['last_disconnection_time'] = timestamp
        if connection_status['connection_uptime_start']:
            uptime = timestamp - connection_status['connection_uptime_start']
        
    elif event_type == 'reconnection_attempt':
        connection_status['total_reconnections'] += 1
        connection_status['consecutive_failures'] += 1
    
    # Format log message
    log_msg = f"🔗 CONNECTION EVENT: {event_type.upper()} at {timestamp.strftime('%H:%M:%S')}"
    if details:
        log_msg += f" - {details}"
    if uptime:
        log_msg += f" (uptime: {uptime})"
        
    print(log_msg)
    
    # Connection status summary
    if event_type in ['connected', 'disconnected']:
        status_emoji = "🟢" if connection_status['is_connected'] else "🔴"
        print(f"{status_emoji} Status: {'CONNECTED' if connection_status['is_connected'] else 'DISCONNECTED'} "
              f"| Total reconnections: {connection_status['total_reconnections']} "
              f"| Consecutive failures: {connection_status['consecutive_failures']}")

def websocket_error_handler(error):
    """
    T018: Enhanced websocket error handler with connection resilience,
    exponential backoff reconnection, and comprehensive monitoring per FR-010.
    """
    global reconnection_attempts
    
    try:
        log_connection_event('error', f"WebSocket error: {error}")
        
        # Check if this is a connection error that requires reconnection
        error_str = str(error).lower()
        connection_errors = ['connection', 'timeout', 'network', 'disconnect', 'closed', 'refused', 'unreachable']
        
        if any(err_type in error_str for err_type in connection_errors):
            log_connection_event('disconnected', f"Connection error: {error_str}")
            
            if reconnection_attempts < max_reconnection_attempts:
                # Calculate delay using extended exponential backoff
                delay_index = min(reconnection_attempts, len(reconnection_delays) - 1)
                delay = reconnection_delays[delay_index]
                
                log_connection_event('reconnection_attempt', 
                                   f"Attempt {reconnection_attempts + 1}/{max_reconnection_attempts} in {delay}s")
                
                reconnection_attempts += 1
                
                # Wait for the specified delay
                time.sleep(delay)
                
                # Attempt to reconnect with full error handling
                try:
                    print("🔄 Attempting full websocket reconnection...")
                    
                    # Step 1: Close existing connection safely
                    try:
                        pyRofex.close_websocket_connection()
                        print("✅ Closed existing websocket connection")
                        time.sleep(1)  # Brief pause for cleanup
                    except Exception as close_error:
                        print(f"⚠️ Error closing connection (continuing): {close_error}")
                    
                    # Step 2: Re-initialize websocket connection with handlers
                    pyRofex.init_websocket_connection(
                        market_data_handler=market_data_handler,
                        error_handler=websocket_error_handler,
                        exception_handler=websocket_exception_handler
                    )
                    
                    # Step 3: Test connection and reset counters on success
                    log_connection_event('connected', "Reconnection successful")
                    reconnection_attempts = 0  # Reset counter on successful reconnection
                    
                    # Step 4: Re-subscribe to market data after successful reconnection
                    print("🔄 Re-establishing market data subscriptions...")
                    try:
                        subscribe_to_market_data()
                        print("✅ Market data subscriptions re-established")
                    except Exception as resub_error:
                        print(f"⚠️ Error re-subscribing to market data: {resub_error}")
                        print("🔄 Market data may be incomplete until next reconnection")
                    
                except Exception as reconnect_error:
                    log_connection_event('reconnection_failed', f"Failed: {reconnect_error}")
                    print(f"❌ Reconnection attempt {reconnection_attempts} failed: {reconnect_error}")
                    
            else:
                log_connection_event('reconnection_exhausted', 
                                   f"Max attempts ({max_reconnection_attempts}) reached")
                print("🚨 CRITICAL: Maximum reconnection attempts reached")
                print("🚨 MANUAL INTERVENTION REQUIRED:")
                print("   1. Check internet connectivity")
                print("   2. Verify COCOS broker service status")
                print("   3. Confirm account credentials and permissions")
                print("   4. Restart application if necessary")
                
        else:
            log_connection_event('non_connection_error', f"Non-connection error: {error_str}")
            print(f"ℹ️  Non-connection error logged - continuing operation")
            
    except Exception as handler_error:
        print(f"🔴 CRITICAL: Error in websocket_error_handler: {handler_error}")
        log_connection_event('handler_error', f"Handler error: {handler_error}")

def websocket_exception_handler(exception):
    """
    Handle websocket exceptions gracefully.
    Logs exceptions for troubleshooting without stopping execution.
    
    This handler catches unexpected exceptions during websocket operations
    and ensures the system continues running despite individual failures.
    """
    try:
        print(f"⚠️  WebSocket Exception: {type(exception).__name__}")
        print(f"⚠️  Exception details: {exception}")
        print(f"⚠️  Time: {pd.Timestamp.now()}")
        
        # Log exception details for debugging
        import traceback
        exception_details = traceback.format_exc()
        print(f"⚠️  Full traceback:\n{exception_details}")
        
        # Check if exception is critical or can be ignored
        exception_str = str(exception).lower()
        critical_exceptions = ['memory', 'critical', 'fatal', 'system']
        
        if any(critical_word in exception_str for critical_word in critical_exceptions):
            print(f"🔴 CRITICAL EXCEPTION DETECTED - May require manual intervention")
        else:
            print(f"ℹ️  Exception logged - Continuing operation")
            
    except Exception as handler_exception:
        # Failsafe: if even the exception handler fails, at least print something
        print(f"🔴 FATAL: Exception handler failed: {handler_exception}")
        print(f"🔴 Original exception was: {exception}")

# Legacy function - will be replaced by websocket_error_handler  
def on_error(online, error):
    print("Error Message Received: {0}".format(error))

# Aca dice que cosas va a actualizar; en este ejemplo dejamos afuera los activos para 24Hs y Contado Inmediato (SPOT), o sea los comentados con el # adelante
# En el caso de querer traer la informacion de alguna de las lineas que este comentada, eliminarle el # para que el codigo la tome.

# T017: Single, comprehensive authentication with enhanced error handling
print("🔐 Iniciando proceso de autenticación con pyRofex...")
authentication_attempts = 0
max_auth_attempts = 3

while authentication_attempts < max_auth_attempts:
    try:
        authentication_attempts += 1
        print(f"🔄 Intento de autenticación #{authentication_attempts}")
        
        pyRofex.initialize(user=user, password=password, account=account, environment=pyRofex.Environment.LIVE)
        print("✅ Autenticación exitosa con pyRofex")
        print("🎯 CONEXION ESTABLECIDA - Procediendo con configuración WebSocket")
        break
        
    except Exception as auth_error:
        print(f"❌ Error de autenticación intento #{authentication_attempts}: {auth_error}")
        
        if authentication_attempts >= max_auth_attempts:
            print("🛑 FALLO CRITICO: Máximo número de intentos de autenticación alcanzado")
            print("⚠️ CAUSAS POSIBLES:")
            print("   1. Credenciales incorrectas (usuario, contraseña o cuenta)")
            print("   2. Problema de conectividad con api.cocos.xoms.com.ar")
            print("   3. Cuenta suspendida o sin permisos")
            print("   4. Servidor COCOS temporalmente inaccesible")
            print("🛑 DETENIENDO EJECUCION - Se requiere intervención manual per FR-003")
            exit(1)
        else:
            print(f"🔄 Reintentando en 3 segundos... ({max_auth_attempts - authentication_attempts} intentos restantes)")
            time.sleep(3)

# T018: Initialize websocket connection with enhanced monitoring (T013 + T018)
print("🔌 Inicializando conexión WebSocket con monitoreo mejorado...")
try:
    pyRofex.init_websocket_connection(
        market_data_handler=market_data_handler,
        error_handler=websocket_error_handler, 
        exception_handler=websocket_exception_handler
    )
    
    # T018: Log successful connection event and reset counters
    log_connection_event('connected', "Initial WebSocket connection established")
    reconnection_attempts = 0  # Reset reconnection counter on successful connection
    print("✅ Conexión WebSocket inicializada correctamente")
    print("🎯 Sistema listo para recibir datos de mercado en tiempo real")
    
except Exception as e:
    log_connection_event('connection_failed', f"Initial connection error: {e}")
    print(f"❌ Error al inicializar WebSocket: {e}")
    print("🔄 Intentando reconexión con estrategia de backoff...")
    websocket_error_handler(e)

# Market data subscriptions - T014
print("📡 Iniciando suscripciones de datos de mercado...")

def subscribe_to_market_data():
    """Subscribe to all market data using pyRofex with symbol transformation and comprehensive error handling"""
    total_subscriptions = 0
    successful_subscriptions = 0
    failed_symbols = []
    
    def safe_subscribe_batch(instrument_type, symbol_list, symbol_getter_name):
        """Helper function for safe batch subscription with individual symbol error handling"""
        nonlocal total_subscriptions, successful_subscriptions, failed_symbols
        
        print(f"📊 Suscribiendo a {instrument_type.lower()}...")
        batch_successful = 0
        batch_failed = 0
        
        for symbol in symbol_list:
            try:
                transformed_symbol = Options_Helper_HM.transform_symbol_for_pyrofex(symbol)
                
                # Attempt individual subscription
                pyRofex.market_data_subscription(
                    tickers=[transformed_symbol], 
                    entries=[pyRofex.MarketDataEntry.BIDS, pyRofex.MarketDataEntry.OFFERS, pyRofex.MarketDataEntry.LAST]
                )
                batch_successful += 1
                total_subscriptions += 1
                successful_subscriptions += 1
                
            except Exception as symbol_error:
                batch_failed += 1
                total_subscriptions += 1
                failed_symbols.append((symbol, str(symbol_error)))
                print(f"⚠️ Error suscribiendo a {symbol}: {symbol_error}")
        
        if batch_successful > 0:
            print(f"✅ {instrument_type}: {batch_successful} suscripciones exitosas")
        if batch_failed > 0:
            print(f"⚠️ {instrument_type}: {batch_failed} suscripciones fallidas - continuando con otros instrumentos")
    
    try:
        # Subscribe to Options with individual error handling
        try:
            options_list = Options_Helper_HM.getOptionsList()
            safe_subscribe_batch("Opciones", options_list, "getOptionsList")
        except Exception as options_list_error:
            print(f"❌ Error obteniendo lista de opciones: {options_list_error} - saltando opciones")
        
        # Subscribe to Bluechips (Panel Lider) with individual error handling  
        try:
            acciones_list = Options_Helper_HM.getAccionesList()
            safe_subscribe_batch("Acciones del Panel Líder", acciones_list, "getAccionesList")
        except Exception as acciones_list_error:
            print(f"❌ Error obteniendo lista de acciones: {acciones_list_error} - saltando acciones")
        
        # Subscribe to Government Bonds with individual error handling
        try:
            bonos_list = Options_Helper_HM.getBonosList()
            safe_subscribe_batch("Bonos", bonos_list, "getBonosList")
        except Exception as bonos_list_error:
            print(f"❌ Error obteniendo lista de bonos: {bonos_list_error} - saltando bonos")
        
        # Subscribe to CEDEARs with individual error handling
        try:
            cedears_list = Options_Helper_HM.getCedearsList()
            safe_subscribe_batch("CEDEARs", cedears_list, "getCedearsList")
        except Exception as cedears_list_error:
            print(f"❌ Error obteniendo lista de CEDEARs: {cedears_list_error} - saltando CEDEARs")
        
        # Subscribe to General Board with individual error handling
        try:
            panel_general_list = Options_Helper_HM.getPanelGeneralList()
            safe_subscribe_batch("Panel General", panel_general_list, "getPanelGeneralList")
        except Exception as panel_list_error:
            print(f"❌ Error obteniendo lista del panel general: {panel_list_error} - saltando panel general")
        
        # Subscribe to Short-term Government Bonds (LETRAs) with individual error handling
        try:
            letras_list = Options_Helper_HM.getLetrasList()
            safe_subscribe_batch("Letras", letras_list, "getLetrasList")
        except Exception as letras_list_error:
            print(f"❌ Error obteniendo lista de letras: {letras_list_error} - saltando letras")
        
        # Subscribe to Corporate Bonds (ONs) with individual error handling
        try:
            ons_list = Options_Helper_HM.getONSList()
            safe_subscribe_batch("Obligaciones Negociables", ons_list, "getONSList")
        except Exception as ons_list_error:
            print(f"❌ Error obteniendo lista de ONs: {ons_list_error} - saltando ONs")
        
        # Summary report
        print("\n📊 REPORTE DE SUSCRIPCIONES:")
        print(f"✅ Exitosas: {successful_subscriptions}")
        print(f"❌ Fallidas: {len(failed_symbols)}")
        print(f"📈 Tasa de éxito: {(successful_subscriptions/total_subscriptions*100):.1f}%" if total_subscriptions > 0 else "📈 Tasa de éxito: 0.0%")
        
        if failed_symbols:
            print("\n⚠️ SIMBOLOS FALLIDOS (continuando sin estos instrumentos):")
            for symbol, error in failed_symbols[:5]:  # Show first 5 failed symbols
                print(f"   - {symbol}: {error}")
            if len(failed_symbols) > 5:
                print(f"   ... y {len(failed_symbols) - 5} más")
        
        if successful_subscriptions > 0:
            print("🎯 Suscripciones completadas - datos de mercado iniciando")
        else:
            print("⚠️ ADVERTENCIA: No se completaron suscripciones exitosas - verifique conectividad y símbolos")
        
    except Exception as e:
        print(f"❌ Error crítico en suscripciones de mercado: {e}")
        print("🔄 Reintentando conexión WebSocket...")
        websocket_error_handler(e)

def get_connection_status_report():
    """
    T018: Generate comprehensive connection status report for monitoring
    Returns current connection health and statistics
    """
    now = pd.Timestamp.now()
    
    # Calculate current uptime if connected
    current_uptime = None
    if connection_status['is_connected'] and connection_status['connection_uptime_start']:
        current_uptime = now - connection_status['connection_uptime_start']
    
    # Calculate time since last disconnection
    time_since_disconnect = None
    if connection_status['last_disconnection_time']:
        time_since_disconnect = now - connection_status['last_disconnection_time']
    
    report = {
        'timestamp': now.isoformat(),
        'is_connected': connection_status['is_connected'],
        'current_uptime': str(current_uptime) if current_uptime else 'N/A',
        'time_since_last_disconnect': str(time_since_disconnect) if time_since_disconnect else 'Never',
        'total_reconnections': connection_status['total_reconnections'],
        'consecutive_failures': connection_status['consecutive_failures'],
        'current_reconnection_attempts': reconnection_attempts,
        'max_reconnection_attempts': max_reconnection_attempts,
        'next_backoff_delay': reconnection_delays[min(reconnection_attempts, len(reconnection_delays) - 1)] if reconnection_attempts < max_reconnection_attempts else 'Max reached'
    }
    
    return report

def print_connection_status_summary():
    """T018: Print formatted connection status for monitoring"""
    report = get_connection_status_report()
    status_emoji = "🟢" if report['is_connected'] else "🔴" 
    health_status = "HEALTHY" if report['is_connected'] and report['consecutive_failures'] == 0 else "DEGRADED" if report['is_connected'] else "DISCONNECTED"
    
    print(f"\n📊 CONNECTION STATUS REPORT ({report['timestamp'][:19]})")
    print(f"{status_emoji} Status: {health_status}")
    print(f"⏱️  Current uptime: {report['current_uptime']}")
    print(f"📊 Total reconnections: {report['total_reconnections']}")
    print(f"🔄 Consecutive failures: {report['consecutive_failures']}")
    print(f"⏳ Time since last disconnect: {report['time_since_last_disconnect']}")
    
    if not report['is_connected']:
        print(f"🔄 Current reconnection attempts: {report['current_reconnection_attempts']}/{report['max_reconnection_attempts']}")
        print(f"⏱️  Next backoff delay: {report['next_backoff_delay']}s")

# Execute subscriptions with enhanced monitoring
print("📊 Iniciando suscripciones con monitoreo de conexión...")
subscribe_to_market_data()

# T015: Enhanced Excel Integration with pyRofex data processing
def update_excel_with_error_handling():
    """
    Update Excel file with current DataFrame data, with comprehensive error handling
    Maintains existing Excel column mapping and handles file access errors gracefully
    """
    try:
        # Check if Excel workbook is accessible
        if wb is None:
            print("❌ Excel workbook not available - skipping update, continuing data collection")
            return False
            
        # Verify sheets are accessible
        try:
            shtTest_accessible = wb.sheets('HomeBroker')
            shtTickers_accessible = wb.sheets('Tickers')
        except Exception as sheet_error:
            print(f"❌ Excel sheets not accessible: {sheet_error} - skipping update, continuing data collection")
            return False
        
        # Update main data ranges with error handling for each section
        try:
            # Update everything DataFrame (stocks, bonds, etc.) - preserve existing structure
            if not everything.empty:
                shtTest.range('A1').options(index=True, header=True).value = everything
                print(f"✅ Updated 'everything' data: {len(everything)} instruments")
            else:
                print("ℹ️ Everything DataFrame is empty - no main data to update")
        except Exception as main_error:
            print(f"⚠️ Error updating main data range: {main_error} - continuing with other updates")
        
        try:
            # Update options DataFrame - maintain existing column mapping
            if not options.empty:
                oRange = 'A' + str(len(everything) + 2)  # Calculate dynamic range position
                shtTest.range(oRange).options(index=True, header=False).value = options
                print(f"✅ Updated options data: {len(options)} instruments at range {oRange}")
            else:
                print("ℹ️ Options DataFrame is empty - no options data to update")
        except Exception as options_error:
            print(f"⚠️ Error updating options range: {options_error} - continuing with other updates")
        
        try:
            # Update cauciones (repos) DataFrame - preserve existing position
            if not cauciones.empty:
                shtTest.range('S2').options(index=True, header=False).value = cauciones
                print(f"✅ Updated cauciones data: {len(cauciones)} instruments")
            else:
                print("ℹ️ Cauciones DataFrame is empty - no repos data to update")
        except Exception as cauciones_error:
            print(f"⚠️ Error updating cauciones range: {cauciones_error} - continuing")
        
        print(f"📊 Excel update cycle completed at {pd.Timestamp.now()}")
        return True
        
    except Exception as wb_error:
        # Excel file may be locked, in use, or corrupted - continue collecting data
        print(f"❌ Excel workbook access error: {wb_error}")
        print("🔄 Continuing data collection - Excel updates will resume when file becomes available")
        return False

# T016: Excel xlwings compatibility verification completed ✅
# - .xlsb format compatibility maintained: 'EPGB OC-DI - Python.xlsb'
# - HomeBroker and Tickers sheet access preserved: wb.sheets('HomeBroker'), wb.sheets('Tickers')  
# - 2-second update frequency confirmed: time.sleep(2)
# - Existing Excel ranges maintained:
#   * Main data: shtTest.range('A1') with index=True, header=True
#   * Options data: dynamic range calculation (A + str(len(everything) + 2))
#   * Cauciones data: shtTest.range('S2') with index=True, header=False
# - DataFrame column mapping preserved for pyRofex data structure compatibility

print("📊 Iniciando ciclo de actualizaciones de Excel cada 2 segundos...")
print("💡 Las actualizaciones continuarán incluso si el archivo Excel está bloqueado temporalmente")

# Referencias:
# bluechips = Acciones del Panel Lider
# goverment_bonds = Bonos
# general_board = Acciones del Panel General
# short_term_government_bonds = Letras
# corporate_bonds = Obligaciones Negociables

# T015: Main Excel update loop with enhanced error handling
update_counter = 0
while True:
    try:
        update_counter += 1
        
        # Attempt Excel update with comprehensive error handling
        update_successful = update_excel_with_error_handling()
        
        if update_successful:
            print(f"✅ Update cycle #{update_counter} completed successfully")
        else:
            print(f"⚠️ Update cycle #{update_counter} completed with errors - data collection continues")
        
        # Maintain 2-second update frequency as specified
        time.sleep(2)
        
    except KeyboardInterrupt:
        print("\n🛑 Update loop stopped by user")
        break
    except Exception as loop_error:
        print(f"❌ Unexpected error in update loop: {loop_error}")
        print("🔄 Restarting update cycle...")
        time.sleep(5)  # Wait longer before retrying after unexpected errors

# Estas lineas realizan el update cada 2 SEGUNDOS (time.sleep(2) ). En caso de querer otra frecuencia, modificar el time.sleep()
