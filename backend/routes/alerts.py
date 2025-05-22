from fastapi import APIRouter, HTTPException, Depends, Path
from fastapi.responses import StreamingResponse
from fastapi.security import HTTPBasic, HTTPBasicCredentials
import httpx
import os
from dotenv import load_dotenv
from models.schemas import Alert, DeviceInfo
from typing import List
import asyncio


load_dotenv()

OBS_USER = os.getenv("API_USERNAME")
OBS_PASS = os.getenv("API_PASSWORD")
router = APIRouter()
security = HTTPBasic()

OBSERVIUM_API_BASE = os.getenv("API_URL")

@router.get(
    "/alerts",
    summary="Download all alerts as JSON",
    description="Fetches all alerts from Observium API and returns them as a downloadable JSON file.",
    response_model=List[Alert],
    tags=["Alerts"]
)
async def Alerts_get_all():
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{OBSERVIUM_API_BASE}/alerts/?pagination=1&pagesize=50",
                auth=(OBS_USER,OBS_PASS)
            )
            if response.status_code != 200:
                raise HTTPException(status_code=response.status_code, detail="Failed to fetch alerts")
            
            alerts_data = response.json()
            raw_alerts = alerts_data.get("alerts", {})
            
            device_ids = {alert.get("device_id") for alert in raw_alerts.values() if alert.get("device_id")}
            async def fetch_device(device_id):
                device_resp = await client.get(
                    f"{OBSERVIUM_API_BASE}/devices/{device_id}",
                    auth=(OBS_USER, OBS_PASS)
                )
                if device_resp.status_code == 200:
                    try:
                        device_json = device_resp.json()
                        if isinstance(device_json, dict):
                            return device_id, device_json.get("device", device_json)
                        else:
                            return device_id, {}
                    except Exception:
                        return device_id, {}
                return device_id, {}
            device_results = await asyncio.gather(*(fetch_device(did) for did in device_ids))
            print(device_results)
            
            devices_map = {str(did): info for did, info in device_results}
            parsed_alerts = []
            for alert in raw_alerts.values():
                device_id = str(alert.get("device_id"))
                device_info = devices_map.get(device_id, {})
                parsed_alert = Alert(
                    alert_table_id=alert.get("alert_table_id"),
                    device_id=device_id,
                    last_ok=alert.get("last_ok"),
                    severity=alert.get("severity"),
                    status=alert.get("status"),
                    recovered=alert.get("recovered"),
                    device={
                        "hostname": device_info.get("hostname"),
                        "ip": device_info.get("ip"),
                        "location": device_info.get("location"),
                        "location_id": device_info.get("location_id"),
                        "location_lat": device_info.get("location_lat"),
                        "location_lon": device_info.get("location_lon"),
                        "sysName": device_info.get("sysName"),
                        "os": device_info.get("os"),
                        "vendor": device_info.get("vendor"),
                        "type": device_info.get("type"),
                        "status": device_info.get("status"),
                    }
                )
                parsed_alerts.append(parsed_alert)
           
            return parsed_alerts

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get(
    "/alerts/{alert_id}",
    summary="Get alert by ID",
    description="Fetches a specific alert from Observium API using the alert ID.",
    tags=["Alerts"]
)
async def Alerts_get_id(alert_id: int = Path(..., description="The ID of the alert to retrieve"),
):
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{OBSERVIUM_API_BASE}/alerts/{alert_id}",
                auth=(OBS_USER,OBS_PASS)
            )

            if response.status_code != 200:
                raise HTTPException(status_code=response.status_code, detail="Failed to fetch alert")
            
            return response.json()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))