from fastapi import APIRouter, HTTPException, Depends, Path
from fastapi.responses import StreamingResponse
from fastapi.security import HTTPBasic, HTTPBasicCredentials
import httpx
import os
from dotenv import load_dotenv
from models.schemas import Alert, DeviceInfo, AlertDB
from typing import List
from supabase import create_client, Client
import asyncio


load_dotenv()

OBS_USER = os.getenv("API_USERNAME") or ""
print(f"OBS_USER: {OBS_USER}")
OBS_PASS = os.getenv("API_PASSWORD") or ""
print(f"OBS_PASS: {OBS_PASS}")
router = APIRouter()
security = HTTPBasic()

OBSERVIUM_API_BASE = os.getenv("API_URL")
print(f"OBSERVIUM_API_BASE: {OBSERVIUM_API_BASE}")

URL = os.getenv("SUPABASE_URL")
KEY = os.getenv("SUPABASE_API_KEY")
if not URL or not KEY:
    raise RuntimeError("SUPABASE_URL and SUPABASE_KEY environment variables must be set")
supabase: Client = create_client(URL, KEY)

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
                    device=DeviceInfo(
                        hostname=device_info.get("hostname"),
                        ip=device_info.get("ip"),
                        location=device_info.get("location"),
                        location_id=device_info.get("location_id"),
                        location_lat=device_info.get("location_lat"),
                        location_lon=device_info.get("location_lon"),
                        sysName=device_info.get("sysName"),
                        os=device_info.get("os"),
                        vendor=device_info.get("vendor"),
                        type=device_info.get("type"),
                        status=device_info.get("status"),
                    ) if device_info else None
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
    
# Esta es la función que el scheduler llama
async def save_alerts_to_db():
    print("⏳ Ejecutando fetch y guardado de alerts en BD...")

    try:
        # Obtener las alertas desde Observium API
        from routes.alerts import Alerts_get_all
        api_alerts = await Alerts_get_all()
        
        # Obtener las alertas existentes de la BD
        db_response = supabase.table("alerts").select("*").execute()
        db_alerts = {str(alert['alert_table_id']): alert for alert in db_response.data}

        # Procesar cada alerta de la API
        for alert in api_alerts:
            alert_id = str(alert.alert_table_id)
            
            # Si la alerta ya existe en la BD
            if alert_id in db_alerts:
                # Si está marcada como completada, la saltamos
                if db_alerts[alert_id].get('completado') == 'SI':
                    continue
                    
                # Si no está completada, actualizamos sus datos pero mantenemos el estado 'completado'
                supabase.table("alerts").update({
                    "device_id": alert.device_id,
                    "last_ok": alert.last_ok,
                    "severity": alert.severity,
                    "status": alert.status,
                    "recovered": alert.recovered,
                    "device": alert.device.dict() if alert.device else {}
                }).eq("alert_table_id", alert_id).execute()
            else:
                # Es una alerta nueva, la insertamos con completado = 'NO'
                supabase.table("alerts").insert({
                    "alert_table_id": alert.alert_table_id,
                    "device_id": alert.device_id,
                    "last_ok": alert.last_ok,
                    "severity": alert.severity,
                    "status": alert.status,
                    "recovered": alert.recovered,
                    "completado": "NO",
                    "device": alert.device.dict() if alert.device else {}
                }).execute()

        print("✅ Alertas actualizadas correctamente.")
        
    except Exception as e:
        print(f"❌ Error al actualizar alertas: {str(e)}")
        raise

@router.get(
    "/alerts_db",
    summary="Get all alerts from DB",
    description="Fetches all alerts stored in the Supabase DB, formatted with DeviceInfo and completado flag.",
    response_model=List[AlertDB],
    tags=["Alerts"]
)
async def Alerts_get_all_from_db():
    try:
        # Traer todas las alertas de la tabla 'alerts'
        response = supabase.table("alerts").select("*").execute()
        error = getattr(response, "error", None)
        if error is not None:
            raise HTTPException(status_code=500, detail=f"Failed to fetch alerts from DB: {getattr(error, 'message', str(error))}")
        
        raw_alerts = response.data  # lista de dicts

        parsed_alerts = []
        for alert in raw_alerts:
            device_info = alert.get("device", {})
            parsed_alert = AlertDB(
                alert_table_id=alert.get("alert_table_id"),
                device_id=alert.get("device_id"),
                last_ok=alert.get("last_ok"),
                severity=alert.get("severity"),
                status=alert.get("status"),
                recovered=alert.get("recovered"),
                completado=alert.get("completado"),
                device=DeviceInfo(
                    hostname=device_info.get("hostname"),
                    ip=device_info.get("ip"),
                    location=device_info.get("location"),
                    location_id=device_info.get("location_id"),
                    location_lat=device_info.get("location_lat"),
                    location_lon=device_info.get("location_lon"),
                    sysName=device_info.get("sysName"),
                    os=device_info.get("os"),
                    vendor=device_info.get("vendor"),
                    type=device_info.get("type"),
                    status=device_info.get("status"),
                ) if device_info else None 
            )
            parsed_alerts.append(parsed_alert)

        return parsed_alerts

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@router.put(
    "/alerts_db/{alert_table_id}/complete",
    summary="Mark alert as completed",
    description="Updates the 'completado' field to 'SI' for a specific alert. ONLY for ADMINISTRATORS.",
    tags=["Alerts"]
)
async def mark_alert_completed(alert_table_id: int = Path(..., description="The ID of the alert to mark as completed")):
    try:
        # Actualizar la alerta en la base de datos
        response = supabase.table("alerts").update({"completado": "SI"}).eq("alert_table_id", alert_table_id).execute()
        
        error = getattr(response, "error", None)
        if error is not None:
            raise HTTPException(status_code=500, detail=f"Failed to update alert: {getattr(error, 'message', str(error))}")
        
        return {"status": "success", "message": "Alert marked as completed"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@router.put(
    "/alerts_db/{alert_table_id}/no_complete",
    summary="Mark alert as no completed",
    description="Updates the 'completado' field to 'NO' for a specific alert. ONLY for ADMINISTRATORS.",
    tags=["Alerts"]
)
async def mark_alert_no_completed(alert_table_id: int = Path(..., description="The ID of the alert to mark as no completed")):
    try:
        # Actualizar la alerta en la base de datos
        response = supabase.table("alerts").update({"completado": "NO"}).eq("alert_table_id", alert_table_id).execute()
        
        error = getattr(response, "error", None)
        if error is not None:
            raise HTTPException(status_code=500, detail=f"Failed to update alert: {getattr(error, 'message', str(error))}")
        
        return {"status": "success", "message": "Alert marked as no completed"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))