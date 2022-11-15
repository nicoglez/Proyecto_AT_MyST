import pandas as pd
import numpy as np
import datetime
from datetime import datetime
import MetaTrader5 as MT5
import pytz


# Función para bajar datos de MT5
def get_MT5_price(symbol: str, start_date: str, end_date: str) -> pd.DataFrame:
    # Cambiar formato de str
    start_date = datetime.strptime(start_date, "%d-%m-%Y")
    end_date = datetime.strptime(end_date, "%d-%m-%Y")

    # Inicializar MT5
    if not MT5.initialize():
        print("initialize() failed, error code =", MT5.last_error())
        quit()

    # Cambiar timezone a UTC
    timezone = pytz.timezone("Etc/UTC")

    # Crear fecha de inicio y final
    year_1, month_1, day_1 = start_date.year, start_date.month, start_date.day
    utc_from = datetime(year_1, month_1, day_1, tzinfo=timezone)
    year_2, month_2, day_2 = end_date.year, end_date.month, end_date.day
    utc_to = datetime(year_2, month_2, day_2, tzinfo=timezone)

    # obtener datos de MT5 de x divisa de start_date a end_date
    rates = MT5.copy_rates_range(symbol.upper(), MT5.TIMEFRAME_D1, utc_from, utc_to)
    # cerrar conexion
    MT5.shutdown() \
        # crear DF
    rates_frame = pd.DataFrame(rates)
    rates_frame['time'] = pd.to_datetime(rates_frame['time'], unit='s')

    return rates_frame
