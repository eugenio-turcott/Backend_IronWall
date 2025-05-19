from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import StreamingResponse
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from typing import Annotated
import httpx
import json
import io

router = APIRouter()
security = HTTPBasic()

OBSERVIUM_API_BASE = "http://201.150.5.213/api/v0"

@router.get(
    "/alerts",
    summary="Download all alerts as JSON",
    description="Fetches all alerts from Observium API and returns them as a downloadable JSON file.",
    response_class=StreamingResponse,
    tags=["Observium"]
)
async def Alerts_get_all(crenditals: Annotated[HTTPBasicCredentials, Depends(security)]):
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{OBSERVIUM_API_BASE}/alerts",
                auth=(crenditals.username,crenditals.password)
            )

            if response.status_code != 200:
                raise HTTPException(status_code=response.status_code, data="Failed to fetch alerts")
            
            alerts_data = response.json()
            print(alerts_data)
            json_bytes = io.BytesIO(json.dumps(alerts_data,indent=2).encode("utf-8"))
            
            return StreamingResponse(
            json_bytes,
            media_type="application/json",
            headers={"Content-Disposition": "attachment; filename=alerts.json"}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
