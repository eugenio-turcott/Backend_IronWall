from fastapi import APIRouter, HTTPException, Depends, Path
from fastapi.responses import StreamingResponse
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from typing import Annotated
import httpx
import os
from dotenv import load_dotenv
import pandas as pd
from statsmodels.tsa.holtwinters import ExponentialSmoothing
import numpy as np
from datetime import datetime, timedelta

load_dotenv() 
OBSERVIUM_API_GRAPH= "http://201.150.5.213/graph.php?timestamp_preset=&update=&requesttoken=541f26df36dbe0d23dd0fb48daf000e68fa985ef87916d79894a58caccc9a90d&type=multi-port_bits_separate&id=WyIzMDM1NTIiLCIzMDM1NTEiLCIyNzA2ODYiLCI4NzE1MiIsIjE5MzMyMSIsIjI3MjIxOSIsIjI0MzY4NiIsIjI0MzcxMCIsIjExOTU1OCIsIjE5NTkzMiIsIjEzNzQyMSIsIjExMDc3OSIsIjEyMzkyNyIsIjM2MjQ5OCIsIjE5MzMyMCIsIjI0MzY4NSIsIjI0MzcwOSIsIjI5NDk3NyIsIjI0MzY4NyIsIjI0MzcxMSIsIjU2NjgiLCIxMzAxNiIsIjgyOTkiLCI4MzAwIiwiMjI2NjMzIiwiMjI2NjM1IiwiMTExOTAzIiwiMTU0Njk5IiwiMTIyODgwIiwiMTAzNjE2IiwiMTk1OTI5IiwiMzg2MDg2IiwiMTEwMDQwIiwiNTAzMyIsIjkyNDc0IiwiMjQ0NDAzIiwiMTQzNTQ0IiwiODEzMzQiLCI4NjQ0OSIsIjg5OTczIiwiMjc2MDU5IiwiNjE4MiIsIjYxODEiLCI1NjAxIiwiMTMwODA4IiwiMzk2ODQ4IiwiOTI4IiwiNjAwNiIsIjEyODExMyIsIjE0MzU0MyIsIjEzMDgwNSIsIjE5NTkzMyIsIjE5NTkzMCIsIjEyODEwOSIsIjg3MTUwIiwiMjc0MTE1IiwiMjY3MDM1IiwiMjI5NjM5IiwiMjQzNzE3IiwiMTk1OTMxIiwiMjM3OTk2IiwiMTQzNTQ2IiwiMTk5MzY1IiwiOTQ2NSIsIjEyMzIwOSIsIjI0MjkyOSIsIjY1NzA2IiwiMTM3NDI2IiwiMTA0ODQ5IiwiMTk2MzY3IiwiMjMwNTAzIiwiMTkxNDk0IiwiMTA3IiwiNTI0ODkiLCI5NzA0MyIsIjg3MTU0IiwiMTAzNjIwIiwiMTk4NTE5IiwiOTcwNDQiLCI2MjkxNyIsIjYyOTU2IiwiMjU3OTMxIiwiODI5MCIsIjkyNCIsIjMzOTQ3MyIsIjM4NjA4MCIsIjEwMzYzNCIsIjM4NjA3OSIsIjcxNzYiLCI4MTMzMyIsIjMwMzU2NyIsIjgwNjgiLCI3MTY2IiwiMTAzMiIsIjI3MTU5IiwiMjU4MjMxIiwiNzE3NSIsIjI1Mjc1MyIsIjcxNzQiLCIyNzMzMjQiLCI3MTY3IiwiMjI2NjQxIiwiMjg4NzIwIiwiMjg4NzIyIiwiMTEyOTg5IiwiMTEzNDE5IiwiMzM5NDc4IiwiMjg4NzIxIl0%3D&legend=no&height=60&width=150&loading=lazy&from=1621805777&to=1747949777&format=json"
OBS_USER = os.getenv("API_USERNAME")
OBS_PASS = os.getenv("API_PASSWORD")
router = APIRouter()
security = HTTPBasic()

@router.get(
    "/graphs",
    summary="Download all graphs as JSON",
    description="Fetches all ports from Observium API and returns them as a downloadable JSON file.",
    tags=["Graphs"]
)
async def get_graph_traffic():
    try:
        if OBS_USER is None or OBS_PASS is None:
            raise HTTPException(status_code=500, detail="API_USERNAME or API_PASSWORD environment variable not set")

        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{OBSERVIUM_API_GRAPH}",
                auth=(str(OBS_USER), str(OBS_PASS))
            )

            if response.status_code != 200:
                raise HTTPException(status_code=response.status_code, detail="Failed to fetch device")

            return response.json()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

def predict_next_year(data, num_series=214):
    """Función robusta para predecir sin valores negativos"""
    predictions = {}
    
    # Si los datos vienen en formato de lista, convertimos a diccionario
    if isinstance(data, list):
        data = {str(i): values for i, values in enumerate(data)}
    
    # Verificamos si tenemos un diccionario válido
    if not isinstance(data, dict):
        raise ValueError("Los datos deben ser un diccionario o una lista")
    
    for key in data:
        values = data[key]
        
        # Procesar valores asegurando que sean números positivos
        processed_values = []
        for x in values if isinstance(values, (list, np.ndarray)) else []:
            try:
                if isinstance(x, str) and 'JS:' in x:
                    val = float(x.split('JS:')[0])
                else:
                    val = float(x)
                processed_values.append(max(0, val))  # Asegurar no negativos
            except (ValueError, TypeError):
                processed_values.append(0.0)
        
        # Si no hay suficientes valores, completar con el último valor válido o cero
        if len(processed_values) < num_series:
            last_val = processed_values[-1] if len(processed_values) > 0 else 0
            processed_values.extend([last_val] * (num_series - len(processed_values)))
        else:
            processed_values = processed_values[:num_series]  # Recortar si es necesario
        
        # Crear modelo de suavizado exponencial
        try:
            with np.errstate(all='ignore'):  # Ignorar warnings numéricos
                model = ExponentialSmoothing(
                    processed_values,
                    trend='add',
                    seasonal='add',
                    seasonal_periods=12
                )
                fit = model.fit()
                forecast = fit.forecast(num_series)
                forecast = [max(0, float(x)) for x in forecast]  # Asegurar no negativos
        except:
            # Fallback: usar el último valor o promedio histórico
            last_value = processed_values[-1] if len(processed_values) > 0 else 0
            avg_value = np.mean(processed_values) if len(processed_values) > 0 else 0
            forecast = [max(0, (last_value + avg_value) / 2)] * num_series
        
        predictions[key] = forecast
    
    return predictions

def format_predictions(predicted_data, historical_structure):
    """Formatea las predicciones para que coincidan con la estructura histórica"""
    # Si los datos históricos son una lista de listas
    if isinstance(historical_structure, list):
        # Convertimos el diccionario de predicciones a lista manteniendo el orden
        return [predicted_data[str(i)] for i in range(len(predicted_data))]
    
    # Si los datos históricos son un diccionario con claves específicas
    elif isinstance(historical_structure, dict):
        # Creamos un nuevo diccionario con las mismas claves
        formatted = {}
        for i, key in enumerate(historical_structure.keys()):
            formatted[key] = predicted_data[str(i)]
        return formatted
    
    return predicted_data  # Fallback por si acaso

@router.get(
    "/graphs/prediction",
    summary="Get traffic data with next year prediction",
    description="Fetches historical traffic data and generates a prediction for the next year.",
    tags=["Graphs"]
)
async def get_graph_traffic_with_prediction():
    try:
        # Obtener datos históricos
        historical_response = await get_graph_traffic()
        
        if not historical_response:
            raise HTTPException(status_code=404, detail="No data received from API")
        
        # Determinar número de series según la leyenda
        num_series = len(historical_response.get('meta', {}).get('legend', [])) or 214
        
        # Generar predicción
        predicted_data = predict_next_year(
            historical_response['data'],
            num_series=num_series
        )
        
        # Formatear las predicciones para que coincidan con la estructura histórica
        formatted_predictions = format_predictions(
            predicted_data,
            historical_response['data']
        )
        
        # Calcular rangos de tiempo
        meta = historical_response.get('meta', {})
        historical_start = meta.get('start', 0)
        historical_end = meta.get('end', 0)
        step = meta.get('step', 86400)  # Valor por defecto: 1 día
        
        # Estructurar respuesta
        response = {
            "meta": {
                "historical_start": historical_start,
                "historical_end": historical_end,
                "prediction_start": historical_end + 31536000,  # +1 año
                "prediction_end": historical_end + 2 * 31536000,  # +2 años
                "step": step,
                "legend": meta.get('legend', []),
                "cutoff_point": historical_end
            },
            "historical": historical_response['data'],
            "prediction": formatted_predictions  # Usamos las predicciones formateadas
        }
        
        return response
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Prediction error: {str(e)}"
        )