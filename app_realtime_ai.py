# app_realtime_ai.py
import time
from datetime import datetime, timedelta
import data_loader
import indicators
import feature_engineering
import ai_logic
import config

def run_ai_monitor():
    # 1. Iniciar conexión
    if not data_loader.initialize_mt5():
        return

    print(f"\n--- MONITOR IA MANOS FUERTES: {config.SYMBOL} ({config.TIMEFRAME}m) ---")
    print(f"   Estrategia: CVD Sintetico + Random Forest")
    print("------------------------------------------------------------------")
    
    if ai_logic.load_model() is None:
        print("XXX DETENIDO: Entrena el modelo primero con 'python train_model.py'")
        return
    
    print(">>> Modelo cargado. Esperando cierre de vela... (Ctrl+C para salir)\n")

    # Variable para recordar la última vela procesada
    last_processed_time = None

    try:
        while True:
            now = datetime.now()
            
            # --- PASO A: Obtener Datos ---
            df_candles = data_loader.get_candles(config.SYMBOL, config.TIMEFRAME, n_candles=500)
            lookback_ticks = now - timedelta(hours=4) 
            df_ticks = data_loader.get_ticks(config.SYMBOL, lookback_ticks, now)
            
            if df_candles is not None and df_ticks is not None:
                
                # --- PASO B: Calcular Indicadores ---
                cvd = indicators.calculate_synthetic_cvd(df_ticks, config.TIMEFRAME_POLARS)
                df_features = feature_engineering.create_dataset(df_candles, cvd)
                
                if not df_features.is_empty():
                    # Tomamos la última vela CERRADA
                    last_closed_candle = df_features.row(-2, named=True)
                    candle_time = last_closed_candle['time']
                    
                    # --- FILTRO: Solo actuar si es una vela nueva ---
                    if candle_time != last_processed_time:
                        last_processed_time = candle_time
                        
                        # --- PASO C: Predicción ---
                        # current_candle solo para mostrar precio actual
                        current_candle = df_features.row(-1, named=True)
                        state_text, signal = ai_logic.predict_market_state(last_closed_candle)
                        
                        # Limpiamos el texto de la IA (quitamos colores internos si los hubiera)
                        # Aunque ai_logic ya devuelve texto limpio, aseguramos formato aquí.
                        clean_state = state_text.replace("IA:", "").strip()
                        
                        # --- PASO D: Mostrar en Consola (Formato Clásico) ---
                        price = last_closed_candle['close']
                        z_val = last_closed_candle['z_score']
                        
                        # Iconos simples de texto
                        icon = "[---]"
                        if signal == 1: icon = "[COMPRA]"
                        elif signal == -1: icon = "[VENTA]"
                        elif "DUDOSA" in clean_state: icon = "[?]"
                        
                        # Imprimir línea limpia
                        print(f"Hora: {candle_time} | Precio: {price:.2f} | Z-Score: {z_val:.2f} | {icon} {clean_state}")
                        
                        # Alerta visual extra con guiones si hay señal
                        if signal != 0:
                            print(f"**************************************************")
                            print(f"*** ALERTA: SENAL DETECTADA -> {icon} ***")
                            print(f"**************************************************")
            
            # Esperar 10 segundos
            time.sleep(10)

    except KeyboardInterrupt:
        print("\nMonitor apagado.")
        import MetaTrader5 as mt5
        mt5.shutdown()
    except Exception as e:
        print(f"Error inesperado: {e}")

if __name__ == "__main__":
    run_ai_monitor()