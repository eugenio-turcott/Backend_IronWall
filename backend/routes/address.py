from fastapi import APIRouter, HTTPException, Query
from typing import List
import httpx
import os
from dotenv import load_dotenv
from supabase import create_client, Client
from pydantic import BaseModel

load_dotenv() 
OBSERVIUM_API_BASE = os.getenv("API_URL")
OBS_USER = os.getenv("API_USERNAME")
OBS_PASS = os.getenv("API_PASSWORD")

router = APIRouter()

URL = os.getenv("SUPABASE_URL")
KEY = os.getenv("SUPABASE_API_KEY")
if not URL or not KEY:
    raise RuntimeError("SUPABASE_URL and SUPABASE_KEY environment variables must be set")
supabase: Client = create_client(URL, KEY)

async def fetch_and_save_device_names():
    """Función para obtener y guardar los nombres de dispositivos"""
    try:
        # Obtener todas las IPs del ipMap (deberías mover esto a configuración)
        ip_map = {
            "172.30.246.": "172.30.246.254",
            "172.30.246.": "172.30.246.254",
            "172.19.255": "172.19.255.23",
            "172.31.14": "172.31.141.1",
            "10.61.5": "10.61.50.1",
            "172.31.11": "172.31.113.1",
            "172.19.25": "172.19.255.6",
            "172.19.3": "172.19.30.1",
            "172.19.6": "172.19.65.1",
            "172.21.25": "172.21.255.6",
            "172.31.243": "172.31.243.10",
            "172.31.11": "172.31.110.1",
            "172.31.5": "172.31.53.1",
            "172.28.": "172.28.0.1",
            "10.61.5": "10.61.50.1",
            "172.19.25": "172.19.255.6",
            "172.19.3": "172.19.30.1",
            "172.19.6": "172.19.65.1",
            "172.19.25": "172.19.255.6",
            "172.19.3": "172.19.30.1",
            "172.22.1": "172.22.16.1",
            "172.24.1": "172.24.13.1",
            "172.24.1": "172.24.13.1",
            "172.31.1.": "172.31.1.100",
            "172.31.1.": "172.31.1.100",
            "10.2.0.": "10.2.0.254",
            "10.1.": "10.1.5.1",
            "172.31.5": "172.31.53.1",
            "172.31.5": "172.31.53.1",
            "172.21.25": "172.21.255.6",
            "172.31.1": "172.31.10.1",
            "172.31.12": "172.31.127.1",
            "10.20.1": "10.20.11.1",
            "172.31.1": "172.31.17.1",
            "172.31.11": "172.31.113.1",
            "172.31.17": "172.31.175.1",
            "172.31.16": "172.31.160.1",
            "172.31.11": "172.31.110.1",
            "172.31.21": "172.31.218.1",
            "10.2.0": "10.2.0.14",
            "10.2.0": "10.2.0.14",
            "172.31.7": "172.31.79.1",
            "172.31.7": "172.31.72.1",
            "172.24.1": "172.24.11.1",
            "172.24.": "172.24.0.1",
            "172.24.1": "172.24.15.1",
            "172.31.12": "172.31.120.1",
            "172.31.11": "172.31.113.1",
            "172.31.7": "172.31.72.1",
            "172.21.25": "172.21.255.6",
            "172.21.25": "172.21.255.6",
            "172.31.12": "172.31.120.1",
            "172.31.14": "172.31.141.1",
            "172.31.6": "172.31.69.1",
            "172.31.5": "172.31.53.1",
            "10.61.5": "10.61.50.1",
            "172.19.3": "172.19.30.1",
            "172.21.25": "172.21.255.6",
            "172.21.25": "172.21.255.6",
            "172.31.11": "172.31.113.1",
            "172.31.33": "172.31.33.52",
            "172.31.3": "172.31.35.1",
            "172.30.31.": "172.30.31.254",
            "172.255.255": "172.255.255.99",
            "10.20.1": "10.20.11.1",
            "172.31.243": "172.31.243.10",
            "172.31.8": "172.31.86.1",
            "172.21.25": "172.21.255.6",
            "172.21.25": "172.21.255.4",
            "172.21.28": "172.21.28.10",
            "10.20.": "10.20.0.1",
            "172.31.": "172.31.2.1",
            "172.31.": "172.31.1.4",
            "172.31.14": "172.31.141.1",
            "172.31.5": "172.31.53.1",
            "172.31.5": "172.31.53.1",
            "172.31.": "172.31.1.4",
            "172.31.": "172.31.2.1",
            "172.31.": "172.31.8.1",
            "172.21.25": "172.21.255.6",
            "172.24.1": "172.24.13.1",
            "172.24.": "172.24.0.1",
            "172.31.1": "172.31.10.1",
            "172.31.5": "172.31.53.1",
            "172.31.1": "172.31.10.1",
            "172.31.241": "172.31.241.10",
            "172.31.17": "172.31.175.1",
            "172.30.246.": "172.30.246.254",
            "172.31.11": "172.31.117.1",
            "172.31.241": "172.31.241.10",
            "172.30.220.": "172.30.220.254",
            "172.31.22": "172.31.220.1",
            "172.30.27.": "172.30.27.254",
            "172.31.241": "172.31.241.10",
            "172.31.8": "172.31.80.1",
            "172.31.241": "172.31.241.10",
            "172.31.4": "172.31.45.1",
            "172.31.241": "172.31.241.10",
            "172.31.1.": "172.31.1.100",
            "172.30.89.": "172.30.89.246",
            "172.30.89.": "172.30.89.246",
            "172.31.5": "172.31.53.1",
            "172.31.1": "172.31.1.68",
            "172.30.89.": "172.30.89.246",
        }
        ip_list = list(ip_map.values())

        # Fetch device names from Observium
        device_names = []
        async with httpx.AsyncClient() as client:
            for ip in ip_list:
                try:
                    response = await client.get(
                        f"{OBSERVIUM_API_BASE}/address/?ipv4_address={ip}",
                        auth=(OBS_USER, OBS_PASS)
                    )
                    
                    if response.status_code != 200:
                        device_names.append(f"core_{ip}")
                        continue

                    addresses = response.json().get("addresses", [])
                    if not addresses or "device_id" not in addresses[0]:
                        device_names.append(f"core_{ip}")
                        continue

                    device_id = addresses[0]["device_id"]
                    response = await client.get(
                        f"{OBSERVIUM_API_BASE}/devices/{device_id}",
                        auth=(OBS_USER, OBS_PASS)
                    )

                    if response.status_code != 200:
                        device_names.append(f"core_{ip}")
                        continue

                    device = response.json().get("device", {})
                    sys_name = device.get("sysName", f"core_{ip}")
                    device_names.append(sys_name)

                except Exception:
                    device_names.append(f"core_{ip}")

        # Crear el mapeo IP -> Nombre
        ip_to_name = {ip: name for ip, name in zip(ip_list, device_names)}

        # Guardar en Supabase (solo mantenemos un registro)
        existing = supabase.table("device_names").select("*").execute()
        if existing.data:
            supabase.table("device_names").delete().neq("id", "").execute()
        
        result = supabase.table("device_names").insert({
            "ip_to_name_map": ip_to_name
        }).execute()

        return {
            "message": "Device names stored successfully",
            "count": len(ip_to_name),
            "id": result.data[0]["id"]
        }

    except Exception as e:
        print(f"Error saving device names: {str(e)}")
        raise

@router.get(
    "/update_device_names",
    summary="Update device names in database",
    description="Fetches device names from Observium and stores them in Supabase",
    tags=["Device Names"]
)
async def update_device_names():
    try:
        return await fetch_and_save_device_names()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get(
    "/get_device_names_db",
    summary="Get stored device names from Supabase",
    description="Retrieves the device names mapping from Supabase database",
    tags=["Device Names"],
    response_model=dict
)
async def get_device_names_from_db():
    try:
        response = supabase.table("device_names").select("*").order("created_at", desc=True).limit(1).execute()
        
        if not response.data:
            raise HTTPException(status_code=404, detail="No device names found in database")
        
        return response.data[0]["ip_to_name_map"]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    
@router.get(
    "/get_device_names",
    summary="Fetch device names for a list of IPs",
    description="Takes a list of IPs and returns the corresponding device names from Observium.",
    tags=["Address"]
)
async def get_device_names(ips: List[str] = Query(..., description="List of IP addresses")):
    try:
        device_names = []

        async with httpx.AsyncClient() as client:
            for ip in ips:
                try:
                    response = await client.get(
                        f"{OBSERVIUM_API_BASE}/address/?ipv4_address={ip}",
                        auth=(OBS_USER, OBS_PASS)
                    )

                    if response.status_code != 200:
                        device_names.append({"ip": ip, "error": "Address lookup failed"})
                        continue

                    addresses = response.json().get("addresses", [])
                    if not addresses or "device_id" not in addresses[0]:
                        device_names.append(f"core_{ip}")  # ← Nueva versión
                        continue

                    device_id = addresses[0]["device_id"]

                    response = await client.get(
                        f"{OBSERVIUM_API_BASE}/devices/{device_id}",
                        auth=(OBS_USER, OBS_PASS)
                    )

                    if response.status_code != 200:
                        device_names.append({"ip": ip, "error": "Device fetch failed"})
                        continue

                    device = response.json().get("device", {})
                    sys_name = device.get("sysName", "Unknown")

                    device_names.append(sys_name)

                except Exception as inner_e:
                    device_names.append({"ip": ip, "error": str(inner_e)})

        return {"results": device_names}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))