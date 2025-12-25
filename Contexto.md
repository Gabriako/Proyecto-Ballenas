# PROYECTO MAESTRO: [Proyecto Ballenas]

## 1. Descripción General
El sistema lo que hace es trabajar con un activo financiero (inicialmente BTCUSD), y generar un sistema de trading en dos etapas. Imaginemos una caja negra. La entrada serán los datos de indicadores (ADX, ATR, EMA, etc.) y de probabilidades de 7 regimenes.

Los regimenes se calcularon desde un archivo llamado Dataset_Con_Regimenes.csv que contiene los datos de 15 meses del BTCUSD y que contiene las siguientes columnas:

# Diccionario de Datos: Dataset_Masivo_Optuna

| Columna | Tipo de Dato | Origen | Descripción |
| :--- | :--- | :--- | :--- |
| **Timestamp** | String | `TimeToString` | Fecha y hora del cierre de la vela (Minuto). Formato `YYYY.MM.DD HH:MM`. |
| **Resultado_Final** | Int | Fijo (`0`) | *Placeholder*. Reservado para la etiqueta objetivo (Target) del modelo (ej. Win/Loss). |
| **Num_Intentos** | Int | Fijo (`0`) | *Placeholder*. Reservado para conteo de intentos o reentradas. |
| **Accion_Inicial** | Int | Fijo (`1`) | *Placeholder*. Indica el tipo de acción simulada (ej. 1 = Buy, -1 = Sell). |
| **ATR_Act** | Float | Sensor | Valor actual del *Average True Range* (Volatilidad absoluta). |
| **ATR_Rel** | Float | Sensor | ATR Relativo (normalizado respecto a un promedio histórico). |
| **EMA_Princ** | Float | Sensor | Valor de la Media Móvil Exponencial Principal (Tendencia base). |
| **ADX_Val** | Float | Sensor | Valor del indicador *ADX* (Fuerza de la tendencia). |
| **Regimen_Actual** | Int | Fijo (`0`) | *Placeholder*. Reservado para clasificación del estado del mercado (Rango/Tendencia). |
| **RSI_Val** | Float | Sensor | Valor del indicador *RSI* (Momentum). |
| **MACD_Val** | Float | Sensor | Valor principal del *MACD*. |
| **DI_Plus** | Float | Sensor | Componente direccional positivo (+DI) del ADX. |
| **DI_Minus** | Float | Sensor | Componente direccional negativo (-DI) del ADX. |
| **EMA_10** | Float | Sensor | Media Móvil Exponencial de 10 periodos. |
| **EMA_20** | Float | Sensor | Media Móvil Exponencial de 20 periodos. |
| **EMA_40** | Float | Sensor | Media Móvil Exponencial de 40 periodos. |
| **EMA_80** | Float | Sensor | Media Móvil Exponencial de 80 periodos. |
| **EMA_160** | Float | Sensor | Media Móvil Exponencial de 160 periodos. |
| **EMA_320** | Float | Sensor | Media Móvil Exponencial de 320 periodos. |
| **SL_Factor_ATR** | Float | Fijo (`3.0`) | Factor multiplicador del ATR usado para calcular la distancia del Stop Loss. |
| **EMA_Princ_Slope** | Float | Sensor | Pendiente (Slope) de la EMA Principal (Velocidad de cambio). |
| **ADX_Diff** | Float | Sensor | Diferencial del ADX respecto a la vela anterior (Aceleración). |
| **RSI_Velocidad** | Float | Sensor | Tasa de cambio del RSI (Velocidad del momentum). |
| **Volumen_Relativo** | Float | Sensor | Relación entre el volumen actual y el volumen promedio. |
| **Close_Price** | Float | `iClose` | Precio de cierre de la vela en M1. |
| **Deal_Ticket** | Int | Fijo (`0`) | *Placeholder*. Reservado para el ID de la transacción en el broker. |
| **Real_Profit** | Float | Fijo (`0`) | *Placeholder*. Reservado para el beneficio futuro calculado (target de regresión). |
| **prob_regimen_0** | Float | Sensor | Probabilidad de estar en regimen 0 - Canal lateral |
| **prob_regimen_1** | Float | Sensor | Probabilidad de estar en regimen 1 - Canal alcista Volatilidad Baja |
| **prob_regimen_2** | Float | Sensor | Probabilidad de estar en regimen 2 - Canal bajista Volatilidad Baja |
| **prob_regimen_3** | Float | Sensor | Probabilidad de estar en regimen 3 - Canal alcista Volatilidad Alta |
| **prob_regimen_4** | Float | Sensor | Probabilidad de estar en regimen 4 - Canal bajista Volatilidad Alta |
| **prob_regimen_5** | Float | Sensor | Probabilidad de estar en regimen 5 - Tendencia Alcista Clara |
| **prob_regimen_6** | Float | Sensor | Probabilidad de estar en regimen 6 - Tendencia Bajista Clara |

Ojo que hay muchas columnas que no se usan en primera instancia

Etapa 1. Sistema manual de ordenes que realizaré tomando los resultados de esta caja negra.
Etapa 2. Sistema automatizado basado en el mismo contexto.

Actualmente hicimos una prueba y creamos un tag de GitHub que se llama v1.0-alpha. Al terminar la Etapa 1 vamos a setear la versión en v1.0-Beta. Y al terminar la Etapa 2, la versión será v2.0-alpha.

## 2. Reglas Críticas (A MEMORIZAR)
- Se deben usar librerias de clasificacion en Python como scikit-learn, redes neuronales y optuna para probar y configurar las mejores opciones.
- A pesar que los datos los obtuvimos desde el tester de MT5, podemos usar y debemos usar la libreria de Metatrader 5 para conectar Python con Metatrader y determinar los parametros para cuando trabajemos en la Etapa 1 y 2.
- Se debe trabajar modularmente en python, creando un arbol de archivos que sean simples de entender y escalables. 
- Lo primero que se debe hacer es crear la estructura de archivos python que se trabajaran en el sistema


## 4. Archivos Clave
- `main.py`: Punto de entrada.
- `db_manager.py`: Lógica SQL.