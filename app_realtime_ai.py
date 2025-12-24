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

    print(f"\n--- 🧠 Monitor IA Manos Fuertes: {config.SYMBOL} ({config.TIMEFRAME}m) ---")
    print(f"   Estrategia: CVD Sintético + Random Forest")
    print("------------------------------------------------------------------")
    
    if ai_logic.load_model() is None:
        print("❌ DETENIDO: Entrena el modelo primero con 'python train_model.py'")
        return
    
    print("✅ Modelo cargado. Esperando cierre de vela... (Ctrl+C para salir)\n")

    # Variable para recordar la última vela que ya avisamos
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
                    # Tomamos la última vela CERRADA (la penúltima de la lista)
                    last_closed_candle = df_features.row(-2, named=True)
                    candle_time = last_closed_candle['time'] # La hora de esa vela
                    
                    # --- FILTRO ANTI-REPETICIÓN ---
                    # Si la hora de esta vela es diferente a la última que procesamos, actuamos.
                    if candle_time != last_processed_time:
                        
                        # Guardamos esta hora para no repetirla
                        last_processed_time = candle_time
                        
                        # --- PASO C: Predicción ---
                        # Usamos 'current_candle' solo para mostrar el precio actual en vivo
                        current_candle = df_features.row(-1, named=True)
                        
                        state_text, signal = ai_logic.predict_market_state(last_closed_candle)
                        
                        # --- PASO D: Mostrar en Consola ---
                        price = current_candle['close']
                        z_val = last_closed_candle['z_score'] # Z-Score de la vela cerrada
                        
                        # Colores
                        RESET = "\033[0m"
                        RED = "\033[91m"
                        GREEN = "\033[92m"
                        YELLOW = "\033[93m"
                        
                        color = RESET
                        icon = ""
                        
                        if signal == 1: 
                            color = GREEN
                            icon = " 🚀 COMPRA"
                        elif signal == -1: 
                            color = RED
                            icon = " 🔻 VENTA"
                        elif "DUDOSA" in state_text:
                            color = YELLOW
                        
                        # Imprimir reporte limpio
                        print(f"[{candle_time}] Cierre: {last_closed_candle['close']:.2f} | Z: {z_val:.2f} | {color}{state_text}{icon}{RESET}")
                        
                        # Si hay señal fuerte, hacemos ruido extra
                        if signal != 0:
                            print(f"   >>> 🔔 ALERTA DE IA: {icon} DETECTADA EN {price:.2f}")
                            print("-" * 60)
            
            # Esperar 10 segundos antes de volver a chequear
            # (Ahora podemos chequear más rápido sin molestar)
            time.sleep(10)

    except KeyboardInterrupt:
        print("\n👋 Monitor apagado.")
        import MetaTrader5 as mt5
        mt5.shutdown()
    except Exception as e:
        print(f"❌ Error inesperado: {e}")

if __name__ == "__main__":
    run_ai_monitor()