import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import polars as pl
import os

# --- CONFIGURACIÓN ---
FILE_PATH = os.path.join("data", "raw", "sesion_ballenas.csv")
UPDATE_INTERVAL_MS = 30 * 1000  # Actualizar cada 30 segundos (suficiente para histórico)
HISTORY_CANDLES = 2880 # 2 Días aprox (60 min * 24 horas * 2)

# Mapa de Colores (Igual al live)
REGIMEN_COLORS = {
    0: "gray",    1: "#90EE90", 2: "#FFCCCC",
    3: "#00FF00", 4: "#FF0000", 5: "#006400", 6: "#8B0000"
}

app = dash.Dash(__name__)
app.title = "Histórico Ballenas IA (48h)"

app.layout = html.Div(style={'backgroundColor': '#0b0b0b', 'color': '#00F0FF', 'height': '100vh', 'padding': '0'}, children=[
    html.H2("PANEL MACRO: HISTORIA RECIENTE (48H)", style={'textAlign': 'center', 'paddingTop': '10px', 'color': '#FFD700'}),
    
    # Gráfico con más altura para ver detalles
    dcc.Graph(id='history-graph', style={'height': '90vh'}),
    
    dcc.Interval(id='interval-history', interval=UPDATE_INTERVAL_MS, n_intervals=0)
])

@app.callback(Output('history-graph', 'figure'),
              [Input('interval-history', 'n_intervals')])
def update_history(n):
    try:
        if not os.path.exists(FILE_PATH):
            return dash.no_update
            
        df = pl.read_csv(FILE_PATH, ignore_errors=True)
        
        # Parseo de fechas
        if "Timestamp" in df.columns:
            try:
                df = df.with_columns(pl.col("Timestamp").str.to_datetime(strict=False).alias("datetime"))
            except:
                df = df.with_columns(pl.int_range(0, df.height).alias("datetime"))
        else:
            df = df.with_columns(pl.int_range(0, df.height).alias("datetime"))

        # FILTRO DE LARGO PLAZO: Tomamos las últimas 2880 velas (2 días)
        if df.height > HISTORY_CANDLES:
            df = df.tail(HISTORY_CANDLES)
            
    except Exception:
        return dash.no_update

    # Construcción del Gráfico Macro
    fig = make_subplots(
        rows=3, cols=1, shared_xaxes=True, vertical_spacing=0.03,
        row_heights=[0.6, 0.20, 0.20], # Más espacio al precio
        subplot_titles=("Acción de Precio (Contexto 48h)", "Acumulación de Ballenas", "Régimen IA")
    )

    # 1. Precio con Range Slider
    fig.add_trace(go.Scatter(x=df["datetime"], y=df["Close_Price"], mode='lines', name='Precio', 
                             line=dict(color='#00F0FF', width=1)), row=1, col=1)
    if "EMA_Princ" in df.columns:
        fig.add_trace(go.Scatter(x=df["datetime"], y=df["EMA_Princ"], mode='lines', name='EMA Trend', 
                                 line=dict(color='#FFD700', dash='dot', width=1)), row=1, col=1)

    # 2. Ballenas (Micro Score)
    if "Micro_Score" in df.columns:
        # Usamos un gráfico de área para ver "zonas" de presión en el tiempo
        fig.add_trace(go.Bar(
            x=df["datetime"], y=df["Micro_Score"],
            marker_color=['#00FF00' if x >= 0 else '#FF0000' for x in df["Micro_Score"].to_list()],
            name='Presión'
        ), row=2, col=1)

    # 3. IA (Régimen)
    if "Regimen_Actual" in df.columns:
        regimenes = df["Regimen_Actual"].to_list()
        colors_reg = [REGIMEN_COLORS.get(r, "white") for r in regimenes]
        fig.add_trace(go.Scatter(
            x=df["datetime"], y=df["Regimen_Actual"], mode='markers',
            marker=dict(size=4, color=colors_reg, symbol='square'), # Cuadrados para ver densidad
            name='IA'
        ), row=3, col=1)

    # ESTÉTICA MACRO
    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor="#0b0b0b", plot_bgcolor="#0b0b0b",
        hovermode="x unified",
        uirevision='constant',
        # RANGE SLIDER: La magia para navegar en el tiempo
        xaxis=dict(
            rangeslider=dict(visible=True), # Barra inferior para hacer zoom
            type="date"
        )
    )
    
    # Ajustes de Ejes
    fig.update_yaxes(gridcolor="#222", row=1, col=1)
    fig.update_yaxes(range=[-0.6, 0.6], gridcolor="#222", row=2, col=1) # Escala ajustada
    fig.update_yaxes(range=[-0.5, 6.5], tickvals=[0,1,2,3,4,5,6], gridcolor="#222", row=3, col=1)

    return fig

if __name__ == '__main__':
    # Usamos otro puerto (8051) para que pueda correr AL MISMO TIEMPO que el live (8050)
    app.run(debug=False, port=8051)