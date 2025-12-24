# ai_logic.py
import joblib
import pandas as pd
import os
import config

_MODEL = None

def load_model():
    """Carga el modelo en memoria (Singleton)"""
    global _MODEL
    if _MODEL is None:
        if os.path.exists(config.MODEL_FILENAME):
            _MODEL = joblib.load(config.MODEL_FILENAME)
        else:
            print(f"⚠️  ADVERTENCIA: No se encontró '{config.MODEL_FILENAME}'. Ejecuta train_model.py")
    return _MODEL

def predict_market_state(row_dict):
    """
    Recibe un diccionario con los valores de la última vela (z_score, trfi, etc.)
    Devuelve texto y señal numérica.
    """
    model = load_model()
    
    if model is None:
        return "ESPERANDO MODELO...", 0
    
    # Orden correcto de las columnas (CRÍTICO para que la IA no se confunda)
    feature_cols = ['z_score', 'trfi', 'cvd_slope', 'momentum_3', 'volatility']
    
    # Crear DataFrame de 1 fila
    X_input = pd.DataFrame([row_dict], columns=feature_cols)
    
    try:
        # 1. Predicción de Clase (-1, 0, 1)
        pred_class = model.predict(X_input)[0]
        
        # 2. Probabilidad (Confianza)
        probs = model.predict_proba(X_input)[0]
        confidence = max(probs) # Tomamos la probabilidad más alta
        
        # Filtro de seguridad:
        # Si la IA no está al menos un 55% segura, mejor no hacer nada.
        if confidence < 0.55:
            return f"IA: DUDOSA ({confidence:.0%})", 0
            
        if pred_class == 1:
            return f"IA: COMPRA ({confidence:.0%})", 1
        elif pred_class == -1:
            return f"IA: VENTA ({confidence:.0%})", -1
        else:
            return "IA: LATERAL", 0
            
    except Exception as e:
        return f"Error IA: {e}", 0