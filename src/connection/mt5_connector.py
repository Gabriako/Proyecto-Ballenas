import MetaTrader5 as mt5
import polars as pl
from datetime import datetime
import sys

class MT5Connector:
    def __init__(self, login=None, password=None, server=None):
        self.login = login
        self.password = password
        self.server = server
        self.connected = False

    def conectar(self):
        """Inicia conexión con MT5. Retorna True si es exitoso."""
        if not mt5.initialize():
            print(f"Error al inicializar MT5: {mt5.last_error()}", file=sys.stderr)
            self.connected = False
            return False
        
        # Si se requieren credenciales específicas (opcional si MT5 ya está logueado)
        if self.login and self.password and self.server:
            authorized = mt5.login(self.login, password=self.password, server=self.server)
            if not authorized:
                print(f"Error de Login: {mt5.last_error()}", file=sys.stderr)
                mt5.shutdown()
                self.connected = False
                return False

        self.connected = True
        return True

    def desconectar(self):
        mt5.shutdown()
        self.connected = False

    def obtener_ticks_recientes(self, symbol: str, num_ticks: int = 1000) -> pl.DataFrame:
        """
        Obtiene los últimos N ticks.
        MANDAMIENTO 7 y 9: Retorna POLARS y solo usa BID/ASK/TIME.
        """
        if not self.connected:
            if not self.conectar():
                return pl.DataFrame() # Retorno vacío si falla

        # Copiar ticks desde el presente hacia atrás
        # COPY_TICKS_ALL trae todo, pero filtraremos severamente
        ticks = mt5.copy_ticks_from(symbol, datetime.now(), num_ticks, mt5.COPY_TICKS_ALL)

        if ticks is None:
            print(f"Error obteniendo ticks para {symbol}", file=sys.stderr)
            return pl.DataFrame()

        # Convertir a Polars directamente desde el array estructurado de numpy
        # Esto es extremadamente eficiente en memoria
        df = pl.from_numpy(ticks)

        # SELECCIÓN QUIRÚRGICA DE DATOS (MANDAMIENTO 9)
        # Descartamos 'last', 'volume', 'flags' para análisis, 
        # aunque flags podría servir para saber si fue buy/sell maker luego.
        # Por ahora, nos centramos en el flujo de precios Bid/Ask.
        
        df_clean = df.select([
            pl.col("time").alias("timestamp_sec"), # Unix timestamp
            pl.col("time_msc").alias("timestamp_ms"), # Milisegundos para alta frecuencia
            pl.col("bid"),
            pl.col("ask")
        ])

        # Crear spread para debug (opcional, pero útil)
        df_clean = df_clean.with_columns(
            (pl.col("ask") - pl.col("bid")).alias("spread")
        )

        return df_clean

    def obtener_simbolo_info(self, symbol: str):
        """Para validar si el mercado está abierto o chequear especificaciones"""
        return mt5.symbol_info(symbol)
    
    # --- AGREGAR ESTO A LA CLASE MT5Connector ---
    def obtener_velas_recientes(self, symbol: str, timeframe=mt5.TIMEFRAME_M1, num_velas: int = 500) -> pl.DataFrame:
        """
        Obtiene velas OHLC para análisis técnico (Contexto).
        """
        if not self.connected:
            if not self.conectar():
                return pl.DataFrame()

        rates = mt5.copy_rates_from(symbol, timeframe, datetime.now(), num_velas)
        
        if rates is None:
            print(f"Error obteniendo velas para {symbol}", file=sys.stderr)
            return pl.DataFrame()

        # Convertir a Polars
        df = pl.from_numpy(rates)
        
        # Seleccionar y limpiar
        df = df.select([
            pl.col("time").alias("timestamp"),
            pl.col("open"),
            pl.col("high"),
            pl.col("low"),
            pl.col("close"),
            pl.col("tick_volume"),
        ])
        
        return df