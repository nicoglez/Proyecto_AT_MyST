from functions import get_MT5_price
import functions as fn

# definir currency
currency="EURUSD"

# Bajar datos con nuestra función
data = get_MT5_price(currency, "01-01-2019", "02-02-2021")

# Separar entre data de entranamiento y prueba
train_data = data[data["time"] <= "01-01-2020"]
test_data = data[data["time"] > "01-01-2020"]

test_dec = fn.est_tec(test_data,fn.bollinger(test_data)[0],fn.stochastic(test_data)[0])
train_dec = fn.est_tec(train_data,fn.bollinger(train_data)[0],fn.stochastic(train_data)[0])
