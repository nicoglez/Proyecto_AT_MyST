from functions import get_MT5_price

# definir currency
currency="EURUSD"

# Bajar datos con nuestra función
data = get_MT5_price(currency, "01-01-2019", "02-02-2021")

# Separar entre data de entranamiento y prueba
test_data = data[data["time"] <= "01-01-2020"]
train_data = data[data["time"] > "01-01-2020"]
