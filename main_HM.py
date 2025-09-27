# Carga de librerias necesarias:

import time
from pyhomebroker import HomeBroker
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





# Aca declara el archivo Excel que va a actualizar
# Importante: Verificar que el nombre coincida exactamente con nuestro archivo de Excel. De lo contrario, modificarlo

# Hojas del excel
wb = xw.Book('EPGB OC-DI - Python.xlsb')
shtTest = wb.sheets('HomeBroker')
shtTickers = wb.sheets('Tickers')

# Datos del broker - la que utilizamos para acceder a la plataforma de HomeBroker
broker = 00
dni = 'xxxxxxxx'
user = 'yyyyyyyy'
password = 'zzzzzzzz'

# Si esta todo bien, aparecera este mensaje y a continuacion empezara a actualizarse la planilla: 
print("OK: ACTUALIZANDO INFORMACION")

def on_options(online, quotes):
    global options
    thisData = quotes
    thisData = thisData.drop(['expiration', 'strike', 'kind'], axis=1)
    thisData['change'] = thisData["change"] / 100
    thisData['datetime'] = pd.to_datetime(thisData['datetime'])
    thisData = thisData.rename(columns={"bid_size": "bidsize", "ask_size": "asksize"})
    options.update(thisData)


def on_securities(online, quotes):
    global ACC

    print(quotes)
    thisData = quotes
    thisData = thisData.reset_index()
    thisData['symbol'] = thisData['symbol'] + ' - ' +  thisData['settlement']
    thisData = thisData.drop(["settlement"], axis=1)
    thisData = thisData.set_index("symbol")
    thisData['change'] = thisData["change"] / 100
    thisData['datetime'] = pd.to_datetime(thisData['datetime'])
    everything.update(thisData)


def on_repos(online, quotes):
    global cauciones
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


def on_error(online, error):
    print("Error Message Received: {0}".format(error))

# Aca dice que cosas va a actualizar; en este ejemplo dejamos afuera los activos para 24Hs y Contado Inmediato (SPOT), o sea los comentados con el # adelante
# En el caso de querer traer la informacion de alguna de las lineas que este comentada, eliminarle el # para que el codigo la tome.

hb = HomeBroker(int(broker), on_options=on_options, on_securities=on_securities,
    on_repos=on_repos, on_error=on_error)

hb.auth.login(dni=dni, user=user, password=password, raise_exception=True)
hb.online.connect()
hb.online.subscribe_options()
hb.online.subscribe_securities('bluechips', '24hs')                       # Acciones del Panel lider - 24hs
hb.online.subscribe_securities('bluechips', 'SPOT')                       # Acciones del Panel lider - Contado Inmediato
hb.online.subscribe_securities('government_bonds', '24hs')                # Bonos - 24hs
hb.online.subscribe_securities('government_bonds', 'SPOT')                # Bonos - Contado Inmediato
hb.online.subscribe_securities('cedears', '24hs')                         # CEDEARS - 24hs
# hb.online.subscribe_securities('cedears', 'SPOT')                       # CEDEARS - Contado Inmediato
hb.online.subscribe_securities('general_board', '24hs')                   # Acciones del Panel general - 24hs
# hb.online.subscribe_securities('general_board', 'SPOT')                 # Acciones del Panel general - Contado Inmediato
hb.online.subscribe_securities('short_term_government_bonds', '24hs')     # LETRAS - 24hs
# hb.online.subscribe_securities('short_term_government_bonds', 'SPOT')   # LETRAS - Contado Inmediato
hb.online.subscribe_securities('corporate_bonds', '24hs')                 # Obligaciones Negociables - 24hs
# hb.online.subscribe_securities('corporate_bonds', 'SPOT')               # Obligaciones Negociables - Contado Inmediato
hb.online.subscribe_repos()


# Referencias:

# bluechips = Acciones del Panel Lider
# goverment_bonds = Bonos
# general_board = Acciones del Panel General
# short_term_government_bonds = Letras
# corporate_bonds = Obligaciones Negociables


while True:
    try:
        oRange = 'A' + str(listLength)
        shtTest.range('A1').options(index=True, header=True).value = everything
        shtTest.range(oRange).options(index=True, header=False).value = options
        shtTest.range('S2').options(index=True, header=False).value = cauciones
        time.sleep(2)

# Estas lineas realizan el update cada 2 SEGUNDOS (time.sleep(2) ). En caso de querer otra frecuencia, modificar el time.sleep()


    except:
        print('Hubo un error al actualizar excel')
