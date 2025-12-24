# indicators.py
import polars as pl
import config

def calculate_synthetic_cvd(df_ticks, timeframe_str):
    """
    CVD Sintético (Polars):
    - Ask sube (+1)
    - Bid baja (-1)
    """
    # 1. Calcular Delta Sintético tick a tick
    # Usamos shift(1) para comparar con el anterior (similar a diff)
    q = df_ticks.lazy().with_columns([
        (pl.col("ask") - pl.col("ask").shift(1)).alias("ask_diff"),
        (pl.col("bid") - pl.col("bid").shift(1)).alias("bid_diff")
    ]).with_columns([
        # Logica: when(condition).then(value).otherwise(value)
        pl.when(pl.col("ask_diff") > 0).then(1).otherwise(0).alias("buy_pressure"),
        pl.when(pl.col("bid_diff") < 0).then(-1).otherwise(0).alias("sell_pressure")
    ]).with_columns(
        (pl.col("buy_pressure") + pl.col("sell_pressure")).alias("synthetic_delta")
    )

    # 2. Agrupar por Velas (Resample dinámico)
    # group_by_dynamic agrupa por intervalos de tiempo (ej. "5m")
    cvd_resampled = (
        q.group_by_dynamic("time", every=timeframe_str)
        .agg(pl.col("synthetic_delta").sum())
        .collect() # Ejecutar LazyFrame
    )
    
    # 3. Calcular Acumulado (CVD Line)
    # fill_null(0) es importante por si hay periodos sin ticks
    cvd_series = cvd_resampled.with_columns(
        pl.col("synthetic_delta").fill_null(0).cum_sum().alias("cvd")
    )
    
    return cvd_series

def calculate_features(df_candles, df_cvd):
    """Calcula Z-Score, TRFI y une el CVD usando Polars"""
    
    # Aseguramos que ambos DataFrames estén ordenados por tiempo para el join
    df_main = df_candles.sort("time")
    df_cvd = df_cvd.sort("time")
    
    # 1. Unir Velas con CVD
    # Join on 'time', left join para mantener todas las velas
    df = df_main.join(df_cvd, on="time", how="left")
    
    # Definir expresiones para cálculo Lazy
    features = df.lazy().with_columns([
        # Rellenar CVD nulos (forward fill) por si alguna vela no tuvo ticks
        pl.col("cvd").forward_fill().fill_null(0)
    ]).with_columns([
        # --- Z-Score ---
        pl.col("close").rolling_mean(window_size=config.Z_WINDOW).alias("mean"),
        pl.col("close").rolling_std(window_size=config.Z_WINDOW).alias("std"),
        
        # --- TRFI (Sin Volumen) ---
        (pl.col("close") - pl.col("close").shift(1)).alias("price_change")
    ]).with_columns([
        # Calculo final Z-Score
        ((pl.col("close") - pl.col("mean")) / pl.col("std")).fill_nan(0).alias("z_score"),
        
        # Calculo TRFI (EMA del cambio de precio)
        # ewm_mean requiere span
        pl.col("price_change").ewm_mean(span=config.TRFI_EMA, adjust=False).alias("trfi"),
        
        # CVD Slope (Pendiente)
        pl.col("cvd").diff().alias("cvd_slope")
    ]).drop_nulls() # Eliminar filas iniciales sin datos suficientes (NaNs)
    
    return features.collect()