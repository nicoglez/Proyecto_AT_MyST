import warnings
import plotly.graph_objects as go
import functions as fn
import plotly.express as px
import pandas as pd

# Funcion para plottear convergencia
def convergence_chart(data: dict, target_y: str):
    fig = px.line(data, y = target_y, title="Convengencia Algoritmo de Optimizacion",
              height=450, width=1000)
    fig.update_xaxes(title="Itter")
    fig.update_yaxes(title="Value")
    fig.update_traces(line_color="black")
    return fig.show()

# Funcion para plottear grafica de evolucion de capital
def capital_chart(evolucion: pd.DataFrame, train_or_test: str):
    fig = px.line(evolucion, x="time", y="evolucion_capital", title=f"Grafica de Evolucion Capital {train_or_test}",
              height=450, width=1000)
    fig.update_xaxes(title="Date")
    fig.update_yaxes(title="Capital")
    fig.update_traces(line_color="black")
    return fig.show()