import matplotlib.pyplot as plt
import warnings
import plotly.graph_objects as go
import functions as fn

#extra
def plot_ao(data):
    data['ao'] = fn.ao(data, 5, 34)
    data = data.dropna().reset_index(drop=True)
    ax2 = plt.subplot2grid((10,1), (7,0), rowspan = 4, colspan = 1)
    for i in range(len(data)-1):
        if data['ao'][i] > data['ao'][i+1]:
            ax2.bar(data.index[i+1], data['ao'][i+1], color = '#f44336')
        else:
            ax2.bar(data.index[i+1], data['ao'][i+1], color = '#26a69a')
    ax2.set_title('EUR/USD AWESOME OSCILLATOR')
    warnings.filterwarnings('ignore')
    warnings.simplefilter('ignore')
    return plt.show()