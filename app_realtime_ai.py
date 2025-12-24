# app_realtime_ai.py
import time
from datetime import datetime, timedelta
import data_loader, indicators, feature_engineering, ai_logic, config

def run():
    if not data_loader.initialize_mt5(): return
    if ai_logic.load_model() is None:
        print("❌ Ejecuta primero: python train_model.py")
        return

    print(f"--- 🧠 Monitor IA: {config.SYMBOL} ---")
    
    try:
        while True:
            # Datos
            now = datetime.now()
            df_c = data_loader.get_candles(config.SYMBOL, config.TIMEFRAME, 500)
            df_t = data_loader.get_ticks(config.SYMBOL, now - timedelta(hours=4), now)
            
            if df_c is not None and df_t is not None:
                # Calculos
                cvd = indicators.calculate_synthetic_cvd(df_t, config.TIMEFRAME_POLARS)
                df = feature_engineering.create_dataset(df_c, cvd)
                
                if not df.is_empty():
                    # Predicción (Penúltima vela cerrada)
                    last = df.row(-2, named=True)
                    curr = df.row(-1, named=True)
                    txt, sig = ai_logic.predict_market_state(last)
                    
                    # Colores
                    color = "\033[92m" if sig==1 else "\033[91m" if sig==-1 else "\033[93m"
                    print(f"[{curr['time']}] P:{curr['close']:.2f} | Z:{curr['z_score']:.2f} | {color}{txt}\033[0m")
            
            time.sleep(20) # Loop cada 20s
            
    except KeyboardInterrupt:
        import MetaTrader5 as mt5; mt5.shutdown()

if __name__ == "__main__":
    run()