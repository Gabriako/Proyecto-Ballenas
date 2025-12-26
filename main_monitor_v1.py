import time
import sys
import os
from colorama import Fore, Back, Style, init

# --- IMPORTACIONES DE MÓDULOS DEL PROYECTO ---
from src.connection.mt5_connector import MT5Connector
from src.features.tick_processor import TickProcessor
from src.features.indicators import TechnicalIndicators

# --- CONFIGURACIÓN GLOBAL ---
SYMBOL = "BTCUSD"        # Símbolo exacto en tu broker (ej. BTCUSD, BTCUSDm, Bitcoin)
WINDOW_TICKS = 1000      # Tamaño de la ventana para análisis de flujo de órdenes (Micro)
WINDOW_VELAS = 300       # Cantidad de velas para cálculo de indicadores (Macro)
REFRESH_RATE = 1         # Segundos entre actualizaciones de pantalla

# Inicializar colorama para autoreset de colores
init(autoreset=True)

def limpiar_consola():
    """Limpia la terminal para dar efecto de dashboard estático."""
    os.system('cls' if os.name == 'nt' else 'clear')

def main():
    limpiar_consola()
    print(Fore.CYAN + Style.BRIGHT + "--- INICIANDO SISTEMA PROYECTO BALLENAS v1.0-alpha ---")
    
    # 1. INICIALIZACIÓN DE MÓDULOS
    try:
        connector = MT5Connector()
        processor = TickProcessor()
        indicators = TechnicalIndicators()
    except Exception as e:
        print(Fore.RED + f"[FATAL] Error cargando módulos: {e}")
        return

    # 2. CONEXIÓN
    if not connector.conectar():
        print(Fore.RED + "Error crítico: No se pudo conectar a MT5. Revisa que la terminal esté abierta.")
        return

    print(Fore.GREEN + f"Conexión establecida. Escaneando símbolo: {SYMBOL}...")
    time.sleep(1)

    # 3. BUCLE PRINCIPAL (LOOP)
    try:
        while True:
            # --- A. OBTENCIÓN DE DATOS MICRO (TICKS) ---
            # Flujo de órdenes inmediato (Bid/Ask)
            df_ticks = connector.obtener_ticks_recientes(SYMBOL, num_ticks=WINDOW_TICKS)
            metrics_micro = processor.procesar_flujo(df_ticks)
            
            # --- B. OBTENCIÓN DE DATOS MACRO (VELAS) ---
            # Contexto de mercado (Tendencia y Volatilidad)
            df_velas = connector.obtener_velas_recientes(SYMBOL, num_velas=WINDOW_VELAS)
            metrics_macro = indicators.calcular_features(df_velas)

            # --- C. RENDERIZADO DEL DASHBOARD ---
            render_dashboard(metrics_micro, metrics_macro, df_ticks)
            
            # --- D. CONTROL DE TIEMPO ---
            time.sleep(REFRESH_RATE)

    except KeyboardInterrupt:
        # Salida elegante con Ctrl+C
        print(Fore.YELLOW + "\n\n[SISTEMA] Interrupción de usuario detectada.")
        print(Fore.YELLOW + "[SISTEMA] Desconectando y cerrando procesos...")
        connector.desconectar()
        print(Fore.CYAN + "Sistema apagado correctamente.")
        sys.exit(0)
        
    except Exception as e:
        print(Fore.RED + f"\n[ERROR CRÍTICO EN LOOP]: {e}")
        connector.desconectar()

def render_dashboard(micro, macro, df_ticks):
    """
    Función de visualización. Dibuja toda la interfaz en la consola.
    """
    limpiar_consola()
    
    # --- ENCABEZADO ---
    titulo = f" BALLENAS MONITOR | {SYMBOL} | Ventana Tics: {micro.get('tick_count', 0)} "
    print(Fore.WHITE + Back.BLUE + Style.BRIGHT + titulo.ljust(60) + Style.RESET_ALL)
    print("-" * 60)
    
    # --- SECCIÓN 1: CONTEXTO MACRO (Velas M1) ---
    if macro:
        tendencia = macro.get('tendencia_macro', 'NEUTRAL')
        precio = macro.get('precio', 0.0)
        ema50 = macro.get('ema_50', 0.0)
        atr = macro.get('atr', 0.0)

        # Color de la tendencia
        if "ALCISTA" in tendencia:
            color_t = Fore.GREEN
        elif "BAJISTA" in tendencia:
            color_t = Fore.RED
        else:
            color_t = Fore.YELLOW
        
        print(f"Tendencia Global: {color_t}{Style.BRIGHT}{tendencia}{Style.RESET_ALL}")
        print(f"Precio Actual   : {Fore.CYAN}{precio}{Style.RESET_ALL}")
        print(f"Estructura      : EMA50 {ema50:.2f} | ATR {atr:.2f}")
    else:
        print(Fore.YELLOW + "Calculando indicadores macro...")

    print("-" * 60)
    
    # --- SECCIÓN 2: FLUJO DE ÓRDENES MICRO (Ticks) ---
    if micro["status"] == "EMPTY":
        print(Fore.RED + "Esperando flujo de ticks suficiente...")
        return

    desbalance = micro['desbalance'] # Rango -1.0 a 1.0
    compras = micro['compras']
    ventas = micro['ventas']
    intensidad = micro.get('intensidad', 0)
    
    # Barra Visual de Presión [-1 ... 0 ... 1]
    bar_length = 30
    # Normalizar de [-1, 1] a [0, bar_length]
    normalized_pos = int((desbalance + 1) / 2 * bar_length)
    normalized_pos = max(0, min(bar_length - 1, normalized_pos))
    
    barra = ["-"] * bar_length
    
    # Determinar estado del flujo
    color_state = Fore.WHITE
    estado_txt = "NEUTRAL"
    marcador = "|"
    
    if desbalance > 0.15:
        color_state = Fore.GREEN
        estado_txt = "PRESIÓN COMPRA (ASK LIFT)"
        marcador = "▲"
    elif desbalance < -0.15:
        color_state = Fore.RED
        estado_txt = "PRESIÓN VENTA (BID HIT)"
        marcador = "▼"
        
    barra[normalized_pos] = f"{Style.BRIGHT}{marcador}{Style.RESET_ALL}{color_state}"
    barra_str = "".join(barra)

    print(f"Flujo Tics      : {color_state}{estado_txt}{Style.RESET_ALL}")
    print(f"Score Delta     : {desbalance:.4f} (Intensidad: {intensidad:.2f})")
    print(f"Balance         : [{color_state}{barra_str}{Style.RESET_ALL}]")
    print(f"Detalle         : {Fore.GREEN}Buy {compras} {Fore.WHITE}vs {Fore.RED}Sell {ventas}{Style.RESET_ALL}")
    
    # --- SECCIÓN 3: ALERTAS DE DIVERGENCIA (FLIP) ---
    # Detectamos contradicciones entre la Tendencia (Macro) y el Flujo (Micro)
    print("-" * 60)
    
    hay_alerta = False
    
    if macro:
        es_bajista = "BAJISTA" in macro['tendencia_macro']
        es_alcista = "ALCISTA" in macro['tendencia_macro']
        
        # Alerta de REVERSIÓN ALCISTA (Suelo)
        # El precio cae (Macro Bajista) pero entran compras agresivas (Micro > 0.25)
        if es_bajista and desbalance > 0.25:
            print(Back.GREEN + Fore.WHITE + Style.BRIGHT + " [!!!] ALERTA BALLENA: ACUMULACIÓN EN CAÍDA (POSIBLE REBOTE) " + Style.RESET_ALL)
            hay_alerta = True
            
        # Alerta de REVERSIÓN BAJISTA (Techo)
        # El precio sube (Macro Alcista) pero entran ventas agresivas (Micro < -0.25)
        elif es_alcista and desbalance < -0.25:
            print(Back.RED + Fore.WHITE + Style.BRIGHT + " [!!!] ALERTA BALLENA: DISTRIBUCIÓN EN SUBIDA (POSIBLE CAÍDA) " + Style.RESET_ALL)
            hay_alerta = True

    if not hay_alerta:
        print(Fore.LIGHTBLACK_EX + "Escaneando anomalías..." + Style.RESET_ALL)
        
    # Mostrar último tick real para debugging visual
    if not df_ticks.is_empty():
        last = df_ticks.tail(1)
        print(f"\n{Fore.LIGHTBLACK_EX}Last Tick: {last['timestamp_ms'][0]} | Bid: {last['bid'][0]} | Ask: {last['ask'][0]}{Style.RESET_ALL}")

if __name__ == "__main__":
    main()