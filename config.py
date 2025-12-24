# config.py

# --- Credenciales MT5 ---
# Dejar en 0 o cadena vacía si el terminal MT5 ya está abierto y logueado.
LOGIN = 0          
PASSWORD = ""      
SERVER = ""        

# --- Configuración del Mercado ---
SYMBOL = "BTCUSD"       # Activo
TIMEFRAME = 1           # 1 Minuto (Entero para MT5)
TIMEFRAME_POLARS = "1m" # String para Polars (1m = 1 minuto)

# --- Parámetros Técnicos ---
# En M1, 20 periodos son 20 minutos de historia inmediata.
Z_WINDOW = 20           # Periodo para Z-Score (Bandas de Bollinger)
TRFI_PERIOD = 13        # Periodo para Force Index
TRFI_EMA = 13           # Suavizado

# --- Machine Learning ---
MODEL_FILENAME = "manos_fuertes_model.pkl"
PREDICTION_HORIZON = 3      # Predecir qué pasará en los próximos 3 minutos
PROFIT_THRESHOLD = 30.0     # (Ajustable) Cuánto debe mover BTC en 3 min para ser "Oportunidad"