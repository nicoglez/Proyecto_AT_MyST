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
import pyswarms as ps
import pandas_datareader.data as web


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

# Funcion para bandas de bollinger
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

# Funcion sthocastic oscillator
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

# funcion de decision de estudios tecnicos
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

# Funcion para simular
def trading_simulation(data: pd.DataFrame, initial_capital: float, max_loss: float,
                       volume: int, stop_loss: float, take_profit: float):
    # Calculo de rendimientos
    rends = data["close"].pct_change().dropna()
    # Estado de la inversion
    state = 0  # no invertido
    # Capital Inicial en lista
    capital = [initial_capital]
    # Valor de entrada a inversion, variable de apoyo
    entry = 0

    # Simulacion
    for obs in range(len(data)):
        # Estado de inversion
        if data["decision"][obs] == 1 and state == 0:  # Si nuestro generador de señal es 1, entramos
            state = 1
            entry = capital[-1] * volume
        elif state == 1 and data["decision"][obs] == -1:  # Si nuestro generador es -1, y estamos invertidos, vendemos
            state = 0
        elif capital[-1] - entry < max_loss:  # Si perdemos mas de nuestra perdida maxima desinvertimos
            state = 0
        else:  # Si nuestro generador no nos dice nada no hacemos nada
            state = state

        # Actualizacion de capital si invertimos o si no
        if state:  # Si invertimos, entramos en t y en t+1 tenemos rendimiento de n activos
            capital.append(capital[obs] * (1 + rends[obs + 1] * volume))
        else:  # Si no invertimos, nuestro capital en tiempo t es igual al de t-1
            capital.append(capital[obs])

        # Cerrar posicion si pasamos STOP LOSS o TAKE PROFIT
        if stop_loss > data["close"][obs]:
            state = 0
        elif take_profit < data["close"][obs]:
            state = 0

    data["evolucion_capital"] = capital[:-1]
    data["evolucion_rends"] = pd.DataFrame(capital[:-1]).pct_change()
    data["profit_acum"] = data["evolucion_capital"] - initial_capital
    data["rend_acum"] = data["evolucion_capital"]/initial_capital - 1
    return data  # capital[:-1]

# Función radio de Sharpe
Sharpe_Ratio = lambda R, rf, sigma: -(R - rf)/sigma

# Función optimización PSO

def PSO_optimization(data: pd.DataFrame, min_volume: int, max_volume: int, min_SL: float,
                     max_SL: float, min_TP: float, max_TP: float):
    # Definir opciones
    options = {'c1': 0.5, 'c2': 0.3, 'w': 0.9}
    
    # Definir bounds en array
    x_max = np.array([max_SL, max_TP, max_volume])
    x_min = np.array([min_SL, min_TP, min_volume])
    bounds = (x_min, x_max)
    
    # Llamar instancia de PSO
    optimizer = ps.single.GlobalBestPSO(n_particles=20, dimensions=3, options=options, bounds=bounds)
    
    #Funcion Heuristica que optimiza sharpe dada la simulacion
    def f(x): 
        res = []

        for i in range(len(x)):
            stop_loss = x[i][0]
            take_profit = x[i][1]
            volume = x[i][2]
            res.append(Sharpe_Ratio(R=trading_simulation(data=data,
                                                         initial_capital=100000, 
                                                         max_loss=1000, 
                                                         stop_loss=stop_loss, 
                                                         take_profit=take_profit,
                                                         volume=volume)["evolucion_rends"].mean(),
                                    rf=0.05, 
                                    sigma=trading_simulation(data=data,
                                                             initial_capital=100000, 
                                                             max_loss=1000, 
                                                             take_profit=take_profit,
                                                             stop_loss=stop_loss, 
                                                             volume=volume)["evolucion_rends"].std()))

        return np.array(res).flatten()
    
    # Realizar optimización
    cost, pos = optimizer.optimize(f, iters=50)
    
    # Definir variables optimizadas 
    SL, TP, Volume = pos[0], pos[1], round(pos[2], 0)
    
    # Historia de convergencia
    history = optimizer.cost_history
    
    return {"Stop_Loss": SL, "Take_Profit": TP, "Volume": Volume, "Ratio_Sharpe": cost, "History": history}

    # Función para descargar precio o precios de cierre
def get_adj_closes(tickers: str, start_date: str = None, end_date: str = None, freq: str = 'd'):
    # Bajar solo un dato si end_date no se da
    end_date = end_date if end_date else start_date or None
    # Bajar cierre de precio ajustado
    closes = web.YahooDailyReader(symbols=tickers, start=start_date, end=end_date, interval=freq).read()['Adj Close']
    # Poner indice de forma ascendente
    closes.sort_index(inplace=True)
    return closes

# Funcion para obtener metricas de nuestra estrategia
def estadisticas_mad(evolucion):
    
    # Bajar datos del SP500
    SP = get_adj_closes('^GSPC', evolucion.iloc[0, 0], evolucion.iloc[-1, 0])
    SP_rends =(SP/SP.shift()-1).dropna().values
    
    # Metricas del portafolio
    mean_portafolio = float((pd.DataFrame([i for i in evolucion["rend_acum"] if i!=0])).dropna().mean())
    rf = .03 # Asumimos rf de 3%
    sdport = float((pd.DataFrame([i for i in evolucion["rend_acum"] if i!=0])).dropna().std())
    beta = np.cov(SP_rends, evolucion["rend_acum"][:len(SP_rends)])[0][0]/np.var(SP_rends)

    # Calcular Sharpe 
    sharpe = round((mean_portafolio - rf)/sdport, 5)
    # Calcular Treynor
    treynor = round((mean_portafolio - rf)/beta, 5)
    # Calcular Alpha de Jensen
    jensen = round(mean_portafolio - (rf + beta*(SP_rends.mean() - rf)), 5)
    
    summary = pd.DataFrame()
    summary["Sharpe_Ratio"] = [sharpe]
    summary["Treynor_Ratio"] = [treynor]
    summary["Jensen_Alpha"] = [jensen]

    return summary