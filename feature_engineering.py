# feature_engineering.py
import polars as pl
import config
import indicators

def create_dataset(df_candles, df_cvd):
    """
    Crea el dataset final para entrenamiento.
    """
    # Obtenemos el DF con indicadores ya calculado
    df = indicators.calculate_features(df_candles, df_cvd)
    
    # Añadimos features extra para la IA
    df = df.lazy().with_columns([
        # RSI Proxy: Media móvil de cambios positivos/negativos (simplificado)
        (pl.col("close") - pl.col("close").shift(3)).alias("momentum_3"),
        
        # Volatilidad (High - Low)
        (pl.col("high") - pl.col("low")).alias("volatility")
    ]).collect()
    
    return df

def add_targets(df):
    """
    Crea las etiquetas (Target) para clasificación.
    Polars usa shift negativo (-n) para mirar al futuro.
    """
    horizon = config.PREDICTION_HORIZON
    threshold = config.PROFIT_THRESHOLD
    
    df_tagged = df.lazy().with_columns([
        # Precio futuro
        pl.col("close").shift(-horizon).alias("future_close")
    ]).with_columns([
        (pl.col("future_close") - pl.col("close")).alias("future_change")
    ]).with_columns([
        # Lógica de clasificación:
        # 1: Sube > Threshold
        # -1: Baja < -Threshold
        # 0: Lateral
        pl.when(pl.col("future_change") > threshold).then(1)
          .when(pl.col("future_change") < -threshold).then(-1)
          .otherwise(0)
          .alias("target")
    ]).drop_nulls().collect() # Borramos las ultimas filas que no tienen futuro
    
    return df_tagged
