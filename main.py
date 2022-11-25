import functions as fn
import data as dt
import visualizations as vs

# Definicion de datos
capital = 100000
stop_loss = 0.001
take_profit = 0.001
currency="EURUSD"

# Visualizacion de datos
dt.data.head()

# Separacion de datos
dt.train_data.head()
dt.test_data.head()

#  Indicadores tecnicos
fn.bollinger(dt.train_data)[1]
fn.stochastic(dt.train_data)[1]
fn.bollinger(dt.test_data)[1]
fn.stochastic(dt.test_data)[1]

# Generacion de señal de compra/venta
train_dec = dt.train_dec
train_dec.head()
test_dec = dt.test_dec
test_dec.head()

# Optimizacion
dic = fn.PSO_optimization(data=test_dec, min_volume=1, max_volume=10, min_SL=0.1, max_SL=1.2, min_TP=1, max_TP=2)
opt_volume = dic.get("Volume")
opt_TP = dic.get("Take_Profit")
opt_SL = dic.get("Stop_Loss")
vs.convergence_chart(dic, "History")

# Simulacion de Backtesting y Train
df_backtest = fn.trading_simulation(data=train_dec, initial_capital=100000, max_loss=1000, volume=opt_volume,
                                    stop_loss=opt_SL, take_profit=opt_TP)
print(f"El valor final de nuestro portafolio en la parte TRAIN fue de ${round(df_backtest.iloc[-1, 11], 2)}")
print(f"Lo que equivale a un rendimiento de {round(df_backtest.iloc[-1, -1]*100, 2)}%")
print(f"Se realizaron un total de {sum([i for i in df_backtest.iloc[:, 10] if i==1])} operaciones")
vs.capital_chart(df_backtest, "Train")

df_prueba = fn.trading_simulation(data=test_dec, initial_capital=100000, max_loss=1000, volume=opt_volume,
                                  stop_loss=opt_SL, take_profit=opt_TP)
print(f"El valor final de nuestro portafolio en la parte TEST fue de ${round(df_prueba.iloc[-1, 11], 2)}")
print(f"Lo que equivale a un rendimiento de {round(df_prueba.iloc[-1, -1]*100, 2)}%")
print(f"Se realizaron un total de {sum([i for i in df_prueba.iloc[:, 10] if i==1])} operaciones")
vs.capital_chart(df_prueba, "Test")

# Estadisticas MAD
fn.estadisticas_mad(df_backtest)
fn.estadisticas_mad(df_prueba)