import pandas as pd
import numpy as np
import datetime
from datetime import datetime
import MetaTrader5 as MT5
import pytz
from ta.volatility import BollingerBands
from ta.momentum import StochasticOscillator
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import warnings


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


def sma(data, period):
    sma = data.rolling(period).mean()
    return sma

def ao(data, period1, period2):
    median = data['close'].rolling(2).median()
    short = sma(median, period1)
    long = sma(median, period2)
    ao = short - long
    ao_df = pd.DataFrame(ao).rename(columns = {'close':'ao'})
    return ao_df

def bollinger(data):
    indicator_bb = BollingerBands(close=data['close'], window=20, window_dev=2)
    bolldata=pd.DataFrame()
    bolldata['bb_bbm'] = indicator_bb.bollinger_mavg()
    bolldata['bb_bbh'] = indicator_bb.bollinger_hband()
    bolldata['bb_bbl'] = indicator_bb.bollinger_lband()
    bolldata['bb_high_signal'] = indicator_bb.bollinger_hband_indicator()
    bolldata['bb_low_signal'] = indicator_bb.bollinger_lband_indicator()
    fig = go.Figure()
    fig.add_trace(go.Scatter(y=data.close, mode='lines',name='close price',line=dict(color='#FF5733', width=2),connectgaps=True))
    fig.add_trace(go.Scatter(y=bolldata.bb_bbh, mode='lines',name='high bollinger',line=dict(color='#1B68A1', width=2),connectgaps=True))
    fig.add_trace(go.Scatter(y=bolldata.bb_bbm, mode='lines',name='middle bollinger',line=dict(color='#8A8B94', width=2),connectgaps=True))
    fig.add_trace(go.Scatter(y=bolldata.bb_bbl, mode='lines',name='low bollinger',line=dict(color='#0190B6', width=2),connectgaps=True,))
    fig.update_layout(title = "Bolligner Bands Graph",yaxis_title='Dolars',xaxis_title='Time')
    warnings.filterwarnings('ignore')
    return bolldata,fig

def stochastic(data):
    indicator_stoc = StochasticOscillator(high=data['high'], low=data['low'], close=data['close'])
    sdata=pd.DataFrame()
    sdata['stochastic'] = indicator_stoc.stoch()
    sdata['stochastic_buy_signal'] = indicator_stoc.stoch() < 20
    sdata['stochastic_sell_signal'] = indicator_stoc.stoch() > 80
    fig = make_subplots(rows=2, cols=1,row_heights=[0.7, 0.3])
    fig.add_trace(go.Scatter(y=sdata.stochastic, mode='lines',name='stochastic',line=dict(color='#8A8B94', width=2),connectgaps=True), row = 1, col=1)
    fig.add_trace(go.Scatter(y=[80]*len(sdata), mode='lines',name='Upper Bound',line=dict(color='#1B68A1', width=2),connectgaps=True), row = 1, col=1)
    fig.add_trace(go.Scatter(y=[20]*len(sdata), mode='lines',name='Lowe Bound',line=dict(color='#FFDF2D', width=2),connectgaps=True), row = 1, col=1)
    fig.add_trace(go.Scatter(y=data.close, mode='lines',name='close price',line=dict(color='#FF5733', width=2),connectgaps=True), row = 2, col=1)
    fig.update_layout(title = "StochasticOscillator",xaxis_title='Time')
    return sdata,fig

def est_tec(price,bol,st):
    price=price.reset_index(drop=True)
    bol=bol.reset_index(drop=True)
    st=st.reset_index(drop=True)
    for i in range(len(price)):
        if bol['bb_low_signal'][i]==1:
            price.loc[i,'bollinger']=1
        elif bol['bb_high_signal'][i]==1:
            price.loc[i,'bollinger']=-1
        elif bol['bb_high_signal'][i]!=1 and bol['bb_low_signal'][i]!=1:
            price.loc[i,'bollinger']=0
        if st['stochastic_buy_signal'][i]==1:
            price.loc[i,'stochastic']=1
        elif st['stochastic_sell_signal'][i]==1:
            price.loc[i,'stochastic']=-1
        elif st['stochastic_sell_signal'][i]!=1 and st['stochastic_buy_signal'][i]!=1:
            price.loc[i,'stochastic']=0
        if price['stochastic'][i]==1 and price['bollinger'][i]==1:
            price.loc[i,'decision']=1
        elif price['stochastic'][i]==-1 and price['bollinger'][i]==-1:
            price.loc[i,'decision']=-1
        else:
            price.loc[i,'decision']=0
    return price