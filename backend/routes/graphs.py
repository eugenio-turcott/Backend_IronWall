from fastapi import APIRouter, HTTPException, Depends, Path
from fastapi.responses import StreamingResponse
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from typing import Annotated
import httpx
import os
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from statsmodels.tsa.holtwinters import ExponentialSmoothing
from prophet import Prophet
from supabase import create_client, Client
from pydantic import BaseModel

OBSERVIUM_API_GRAPH = os.getenv("OBSERVIUM_API_GRAPH")
OBS_USER = os.getenv("API_USERNAME")
OBS_PASS = os.getenv("API_PASSWORD")
router = APIRouter()
security = HTTPBasic()

URL = os.getenv("SUPABASE_URL")
KEY = os.getenv("SUPABASE_API_KEY")
if not URL or not KEY:
    raise RuntimeError("SUPABASE_URL and SUPABASE_KEY environment variables must be set")
supabase: Client = create_client(URL, KEY)

class GraphData(BaseModel):
    response: dict  # Aquí aceptamos cualquier estructura JSON

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

async def fetch_graph_data():
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

@router.get(
    "/graphs_prediction",
    summary="Get graph data with 12-month prediction (Prophet)",
    description="Returns graph data extended with 12-month predictions for each valid time series using Prophet",
    tags=["Graphs"]
)
async def get_graph_prediction():
    try:
        original_data = await fetch_graph_data()

        original_end = original_data['meta']['end']
        prediction_start = original_end
        prediction_end = original_end + (36 * 30 * 24 * 3600)

        response_data = {
            "meta": {
                "start": original_data['meta']['start'],
                "end": original_data['meta']['end'],
                "start_prediction": prediction_start,
                "end_prediction": prediction_end,
                "step": original_data['meta']['step'],
                "legend": original_data['meta']['legend'],
                "gprints": original_data['meta']['gprints'],
                "rules": original_data['meta']['rules']
            },
            "data": [day.copy() for day in original_data['data']]
        }

        num_ips = len(original_data['meta']['legend']) // 2
        freq_seconds = original_data['meta']['step']
        freq_days = freq_seconds / 86400

        for i in range(num_ips):
            pos_idx = i
            neg_idx = i + num_ips

            for idx, is_negative in [(pos_idx, False), (neg_idx, True)]:
                values = []
                dates = []
                for day_idx, day_values in enumerate(original_data['data']):
                    if isinstance(day_values, list) and idx < len(day_values):
                        value = day_values[idx]
                        if value is not None:
                            ts = datetime.fromtimestamp(original_data['meta']['start']) + timedelta(days=day_idx * freq_days)
                            values.append(-value if is_negative else value)
                            dates.append(ts)

                if len(values) < 10:
                    continue

                df = pd.DataFrame({'ds': dates, 'y': values})
                try:
                    model = Prophet(daily_seasonality=True)
                    model.fit(df)
                    future = model.make_future_dataframe(periods=12, freq='30D')
                    forecast = model.predict(future)

                    pred_values = forecast.tail(36)['yhat'].tolist()

                    last_day = len(original_data['data'])
                    for j, val in enumerate(pred_values):
                        day_idx = last_day + j
                        while len(response_data['data']) <= day_idx:
                            response_data['data'].append([None] * len(original_data['meta']['legend']))
                        response_data['data'][day_idx][idx] = -abs(val) if is_negative else max(0, val)

                except Exception as e:
                    print(f"Failed to predict using Prophet for index {idx}: {str(e)}")

        return response_data

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

async def save_graph_data():
    """Función async para guardar datos de gráficos, manteniendo solo un registro en la tabla"""
    try:
        # Obtener datos de la API
        data = await fetch_graph_data()
        
        # Verificar y limpiar registros existentes
        existing = supabase.table("graphs").select("*").execute()
        if len(existing.data) > 0:
            # Eliminar todos los registros existentes
            supabase.table("graphs").delete().neq("id", "").execute()
        
        # Insertar el nuevo registro
        result = supabase.table("graphs").insert({
            "response": data
        }).execute()
        
        return {
            "message": "Graph data stored successfully",
            "id": result.data[0]["id"]
        }
    except Exception as e:
        print(f"Error saving graph data: {str(e)}")
        raise

async def save_prediction_data():
    """Función async para guardar datos de predicción, manteniendo solo un registro en la tabla"""
    try:
        # Obtener datos de predicción
        prediction_data = await get_graph_prediction()
        
        # Verificar y limpiar registros existentes
        existing = supabase.table("graphs_prediction").select("*").execute()
        if len(existing.data) > 0:
            # Eliminar todos los registros existentes
            supabase.table("graphs_prediction").delete().neq("id", "").execute()
        
        # Insertar el nuevo registro
        result = supabase.table("graphs_prediction").insert({
            "response": prediction_data
        }).execute()
        
        return {
            "message": "Prediction data stored successfully",
            "id": result.data[0]["id"]
        }
    except Exception as e:
        print(f"Error saving prediction data: {str(e)}")
        raise

@router.get(
    "/graphs_db",
    summary="Get stored graph data from Supabase",
    description="Retrieves the latest graph data stored in Supabase database",
    tags=["Graphs DB"],
    response_model=dict  # Esto ayuda a la documentación de OpenAPI
)
async def get_graphs_from_db():
    try:
        # Obtener el único registro de la tabla graphs
        response = supabase.table("graphs").select("response").execute()
        
        if not response.data:
            raise HTTPException(status_code=404, detail="No graph data found in database")
        
        # Retornar directamente el contenido del campo response
        return response.data[0]["response"]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    
@router.get(
    "/graphs_prediction_db",
    summary="Get stored prediction data from Supabase",
    description="Retrieves the latest prediction data stored in Supabase database",
    tags=["Graphs DB"],
    response_model=dict  # Esto ayuda a la documentación de OpenAPI
)
async def get_prediction_from_db():
    try:
        # Obtener el único registro de la tabla graphs_prediction
        response = supabase.table("graphs_prediction").select("response").execute()
        
        if not response.data:
            raise HTTPException(status_code=404, detail="No prediction data found in database")
        
        # Retornar directamente el contenido del campo response
        return response.data[0]["response"]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")