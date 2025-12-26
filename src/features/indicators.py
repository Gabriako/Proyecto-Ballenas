import polars as pl
import numpy as np

class TechnicalIndicators:
    def __init__(self):
        pass

    def calcular_features(self, df_velas: pl.DataFrame) -> dict:
        """
        Calcula indicadores técnicos básicos para definir el régimen.
        Retorna un diccionario con el estado actual.
        """
        if df_velas.is_empty():
            return {}

        # 1. Calcular EMA Principal (ej. 200 periodos para tendencia macro o 50 para intradía)
        # Polars ewm_mean es equivalente a EMA
        df_ind = df_velas.with_columns([
            pl.col("close").ewm_mean(span=50, adjust=False).alias("ema_rapida"),
            pl.col("close").ewm_mean(span=200, adjust=False).alias("ema_lenta")
        ])

        # 2. Calcular ATR (Volatilidad) - Manual en Polars
        # TR = Max(High-Low, Abs(High-PrevClose), Abs(Low-PrevClose))
        df_ind = df_ind.with_columns(
            pl.col("close").shift(1).alias("prev_close")
        ).drop_nulls()

        df_ind = df_ind.with_columns(
            pl.max_horizontal([
                pl.col("high") - pl.col("low"),
                (pl.col("high") - pl.col("prev_close")).abs(),
                (pl.col("low") - pl.col("prev_close")).abs()
            ]).alias("tr")
        )

        # ATR de 14 periodos
        df_ind = df_ind.with_columns(
            pl.col("tr").ewm_mean(span=14, adjust=False).alias("atr")
        )

        # Obtener última fila (Estado actual)
        ultimo = df_ind.tail(1)
        
        precio_actual = ultimo["close"][0]
        ema_rapida = ultimo["ema_rapida"][0]
        ema_lenta = ultimo["ema_lenta"][0]
        atr = ultimo["atr"][0]

        # Determinar Tendencia
        tendencia = "NEUTRAL"
        if precio_actual > ema_rapida > ema_lenta:
            tendencia = "ALCISTA (BULL)"
        elif precio_actual < ema_rapida < ema_lenta:
            tendencia = "BAJISTA (BEAR)"
        
        return {
            "precio": precio_actual,
            "ema_50": ema_rapida,
            "ema_200": ema_lenta,
            "atr": atr,
            "tendencia_macro": tendencia
        }