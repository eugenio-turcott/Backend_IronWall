from fastapi import APIRouter, HTTPException, Depends, Path
from fastapi.responses import StreamingResponse
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from typing import Annotated
import httpx
import json
import io
import os
from dotenv import load_dotenv

load_dotenv()  

OBSERVIUM_API_BASE = os.getenv("API_URL")
OBS_USER = os.getenv("API_USERNAME")
OBS_PASS = os.getenv("API_PASSWORD")
router = APIRouter()
security = HTTPBasic()

@router.get(
    "/ports",
    summary="Download all ports as JSON",
    description="Fetches all ports from Observium API and returns them as a downloadable JSON file.",
    tags=["Ports"]
)
async def Ports_get_all():
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{OBSERVIUM_API_BASE}/ports",
                auth=(OBS_USER,OBS_PASS)
            )

            if response.status_code != 200:
                raise HTTPException(status_code=response.status_code, detail="Failed to fetch device")
            
            port_data = response.json()
            json_bytes = io.BytesIO(json.dumps(port_data,indent=2).encode("utf-8"))
            
            return port_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get(
    "/ports/{port_id}",
    summary="Get ports by ID",
    description="Fetches a specific device from Observium API using the alert ID.",
    tags=["Ports"]
)
async def Ports_get_id(port_id: int = Path(..., description="The ID of the alert to retrieve"),
):
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{OBSERVIUM_API_BASE}/ports/{port_id}",
                auth=(OBS_USER,OBS_PASS)
            )

            if response.status_code != 200:
                raise HTTPException(status_code=response.status_code, detail="Failed to fetch device")
            
            return response.json()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))