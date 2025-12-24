# data_loader.py
import MetaTrader5 as mt5
import polars as pl
from datetime import datetime
import config

def initialize_mt5():
    """Inicia la conexión con MT5"""
    if not mt5.initialize():
        print("Error al iniciar MT5:", mt5.last_error())
        # Solo intentamos login si el usuario puso credenciales en config
        if config.LOGIN != 0 and config.PASSWORD != "":
            authorized = mt5.login(config.LOGIN, password=config.PASSWORD, server=config.SERVER)
            if not authorized:
                print("Fallo en autorización:", mt5.last_error())
                return False
    return True

def get_candles(symbol, timeframe_min, n_candles=1000):
    """Descarga velas OHLC y retorna Polars DataFrame"""
    tf_map = {
        1: mt5.TIMEFRAME_M1, 
        5: mt5.TIMEFRAME_M5, 
        15: mt5.TIMEFRAME_M15, 
        60: mt5.TIMEFRAME_H1
    }
    
    selected_tf = tf_map.get(timeframe_min, mt5.TIMEFRAME_M5)
    
    # Descargar datos (retorna numpy array estructurado)
    rates = mt5.copy_rates_from_pos(symbol, selected_tf, 0, n_candles)
    
    if rates is None or len(rates) == 0:
        print(f"No se pudieron obtener velas para {symbol}")
        return None
        
    # Crear DataFrame Polars directo desde numpy
    # Convertimos tiempo de segundos a Datetime nativo
    df = pl.from_numpy(rates).with_columns(
        pl.from_epoch(pl.col("time"), time_unit="s").alias("time")
    ).sort("time")
    
    return df

def get_ticks(symbol, date_from, date_to=None):
    """
    Descarga ticks BID/ASK usando Polars.
    Solo traemos flags, time, bid, ask (COPY_TICKS_INFO).
    """
    if date_to is None:
        date_to = datetime.now()
        
    ticks = mt5.copy_ticks_range(symbol, date_from, date_to, mt5.COPY_TICKS_INFO)
    
    if ticks is None or len(ticks) == 0:
        print("No se recibieron ticks.")
        return None
        
    # Polars DataFrame
    df = pl.from_numpy(ticks).select([
        pl.col("time"),
        pl.col("bid"),
        pl.col("ask")
    ]).with_columns(
        pl.from_epoch(pl.col("time"), time_unit="s").alias("time")
    ).sort("time")
    
    return df
