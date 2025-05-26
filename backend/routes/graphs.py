from fastapi import APIRouter, HTTPException, Depends, Path
from fastapi.responses import StreamingResponse
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from typing import Annotated
import httpx
import os
from dotenv import load_dotenv
import pandas as pd
import numpy as np
from statsmodels.tsa.arima.model import ARIMA
from datetime import datetime, timedelta
import json

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

def predict_next_year(data):
    """Predicts data for the next year using ARIMA model for each time series"""
    predictions = {
        "about": "ARIMA predicted data for next year",
        "meta": {
            "original_start": data["meta"]["start"],
            "original_end": data["meta"]["end"],
            "predicted_start": data["meta"]["end"] + data["meta"]["step"],
            "predicted_end": data["meta"]["end"] + (365 * 24 * 3600),
            "step": data["meta"]["step"],
            "model": "ARIMA(5,1,0)",
            "legend": data["meta"]["legend"]
        },
        "data": []
    }
    
    # For each time point in the data
    for i in range(len(data["data"])):
        series_data = data["data"][i]
        
        # Skip if data is empty or all null
        if not series_data or all(v is None for v in series_data):
            continue
            
        # Convert to pandas Series and clean data
        s = pd.Series(series_data)
        s = s.replace([None, "null", "0.0JS:0"], np.nan)
        s = s.interpolate()
        
        # Fit ARIMA model
        try:
            model = ARIMA(s, order=(5,1,0))
            model_fit = model.fit()
            
            # Forecast next year (365 days)
            forecast = model_fit.forecast(steps=365)
            
            # Add predicted data to results
            predictions["data"].append(forecast.tolist())
            
        except Exception as e:
            print(f"Error predicting series {i}: {str(e)}")
            # If prediction fails, fill with None
            predictions["data"].append([None] * 365)
    
    return predictions

@router.get(
    "/graphs/prediction",
    summary="Get network traffic prediction for next year",
    description="Uses ARIMA model to predict network traffic for the next year based on historical data",
    tags=["Graphs"]
)
async def get_graph_prediction():
    try:
        if OBS_USER is None or OBS_PASS is None:
            raise HTTPException(status_code=500, detail="API_USERNAME or API_PASSWORD environment variable not set")

        async with httpx.AsyncClient() as client:
            # First get the historical data
            response = await client.get(
                OBSERVIUM_API_GRAPH,
                auth=(str(OBS_USER), str(OBS_PASS))
            )

            if response.status_code != 200:
                raise HTTPException(status_code=response.status_code, detail="Failed to fetch device data")

            historical_data = response.json()
            
            # Predict next year
            predicted_data = predict_next_year(historical_data)
            
            return predicted_data
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))