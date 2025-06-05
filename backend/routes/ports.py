from fastapi import APIRouter, HTTPException, Depends, Path
from fastapi.responses import StreamingResponse
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from typing import Annotated
import httpx
import json
import io
import os
from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv()  

OBSERVIUM_API_BASE = os.getenv("API_URL")
OBS_USER = os.getenv("API_USERNAME")
OBS_PASS = os.getenv("API_PASSWORD")
router = APIRouter()
security = HTTPBasic()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_API_KEY")
if not SUPABASE_URL or not SUPABASE_KEY:
    raise RuntimeError("SUPABASE_URL and SUPABASE_API_KEY environment variables must be set")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

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
    "/ports/total-consumption",
    summary="Get total bandwidth consumption across all ports",
    description="Sums the ifInOctets and ifOutOctets from all ports in Observium.",
    tags=["Ports"]
)
async def get_total_port_consumption():
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{OBSERVIUM_API_BASE}/ports",
                auth=(OBS_USER, OBS_PASS)
            )

            if response.status_code != 200:
                raise HTTPException(status_code=response.status_code, detail="Failed to fetch ports")

            ports_data = response.json().get("ports", {})
            total_in = 0
            total_out = 0

            for port in ports_data.values():
                try:
                    total_in += int(port.get("ifInOctets", 0))
                    total_out += int(port.get("ifOutOctets", 0))
                except (ValueError, TypeError):
                    continue

            return {
                "total_in_octets": total_in,
                "total_out_octets": total_out,
                "total_combined_octets": total_in + total_out,
                "total_in_gb": round(total_in / (1024 ** 3), 2),
                "total_out_gb": round(total_out / (1024 ** 3), 2),
                "total_combined_gb": round((total_in + total_out) / (1024 ** 3), 2)
            }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
@router.get(
    "/ports/total-consumption-internet",
    summary="Get total bandwidth consumption across all internet border ports",
    description="Sums the ifInOctets and ifOutOctets from all ports in Observium.",
    tags=["Ports"]
)
async def get_total_port_consumption_intenet():
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{OBSERVIUM_API_BASE}/ports/?port_descr_type=peering",
                auth=(OBS_USER, OBS_PASS)
            )

            if response.status_code != 200:
                raise HTTPException(status_code=response.status_code, detail="Failed to fetch ports")

            ports_data = response.json().get("ports", {})
            total_in = 0
            total_out = 0

            for port in ports_data.values():
                try:
                    total_in += int(port.get("ifInOctets", 0))
                    total_out += int(port.get("ifOutOctets", 0))
                except (ValueError, TypeError):
                    continue

            return {
                "total_in_octets": total_in,
                "total_out_octets": total_out,
                "total_combined_octets": total_in + total_out,
                "total_in_gb": round(total_in / (1024 ** 3), 2),
                "total_out_gb": round(total_out / (1024 ** 3), 2),
                "total_combined_gb": round((total_in + total_out) / (1024 ** 3), 2)
            }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

async def save_internet_consumption_data():
    """Guarda datos de consumo internet en Supabase"""
    try:
        data = await get_total_port_consumption_intenet()
        
        # Limpiar tabla existente
        existing = supabase.table("consumption_internet").select("*").execute()
        if existing.data:
            supabase.table("consumption_internet").delete().neq("id", "").execute()
        
        # Insertar nuevo registro
        result = supabase.table("consumption_internet").insert({"response": data}).execute()
        return {"message": "Internet consumption data stored", "id": result.data[0]["id"]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error saving internet consumption: {str(e)}")
    
@router.get(
    "/ports/consumption-internet-db",
    summary="Get stored internet consumption data",
    description="Retrieves internet consumption data from Supabase",
    tags=["Ports DB"]
)
async def get_internet_consumption_from_db():
    try:
        response = supabase.table("consumption_internet").select("response").execute()
        if not response.data:
            raise HTTPException(status_code=404, detail="No internet consumption data found")
        return response.data[0]["response"]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get(
    "/ports/total-consumption-nonInternet",
    summary="Get total bandwidth consumption across all non-internet ports",
    description="Sums the ifInOctets and ifOutOctets from all ports in Observium.",
    tags=["Ports"]
)
async def get_total_port_consumption_non_intenet():
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{OBSERVIUM_API_BASE}/ports/?port_descr_type=transit",
                auth=(OBS_USER, OBS_PASS)
            )

            if response.status_code != 200:
                raise HTTPException(status_code=response.status_code, detail="Failed to fetch ports")

            ports_data = response.json().get("ports", {})
            total_in = 0
            total_out = 0

            for port in ports_data.values():
                try:
                    total_in += int(port.get("ifInOctets", 0))
                    total_out += int(port.get("ifOutOctets", 0))
                except (ValueError, TypeError):
                    continue

            return {
                "total_in_octets": total_in,
                "total_out_octets": total_out,
                "total_combined_octets": total_in + total_out,
                "total_in_gb": round(total_in / (1024 ** 3), 2),
                "total_out_gb": round(total_out / (1024 ** 3), 2),
                "total_combined_gb": round((total_in + total_out) / (1024 ** 3), 2)
            }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

async def save_non_internet_consumption_data():
    """Guarda datos de consumo no-internet en Supabase"""
    try:
        data = await get_total_port_consumption_non_intenet()
        
        # Limpiar tabla existente
        existing = supabase.table("consumption_non_internet").select("*").execute()
        if existing.data:
            supabase.table("consumption_non_internet").delete().neq("id", "").execute()
        
        # Insertar nuevo registro
        result = supabase.table("consumption_non_internet").insert({"response": data}).execute()
        return {"message": "Non-internet consumption data stored", "id": result.data[0]["id"]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error saving non-internet consumption: {str(e)}")

@router.get(
    "/ports/consumption-non-internet-db",
    summary="Get stored non-internet consumption data",
    description="Retrieves non-internet consumption data from Supabase",
    tags=["Ports DB"]
)
async def get_non_internet_consumption_from_db():
    try:
        response = supabase.table("consumption_non_internet").select("response").execute()
        if not response.data:
            raise HTTPException(status_code=404, detail="No non-internet consumption data found")
        return response.data[0]["response"]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@router.get(
    "/ports/peering",
    summary="Get total bandwidth consumption across all non-internet ports",
    description="Sums the ifInOctets and ifOutOctets from all ports in Observium.",
    tags=["Ports"]
)
async def get_non_internet():
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{OBSERVIUM_API_BASE}/ports/?port_descr_type=transit",
                auth=(OBS_USER, OBS_PASS)
            )

            if response.status_code != 200:
                raise HTTPException(status_code=response.status_code, detail="Failed to fetch ports")
            
            return response.json

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@router.get(
    "/ports/failures",
    summary="Get devices with top port failures",
    description="Fetches devices with top port failures Observium API.",
    tags=["Ports"]
)
async def get_top_failures():
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{OBSERVIUM_API_BASE}/ports/?state=down&ignore=0",
                auth=(OBS_USER,OBS_PASS)
            )
            if response.status_code != 200:
                raise HTTPException(status_code=response.status_code, detail="Failed to fetch device")
            data = response.json()
            failures = {}

            for port in data.get("ports", {}).values():
                device = port.get("sysName") or port.get("hostname") or "Unknown"
                port_label = port.get("ifDescr") or port.get("port_label") or str(port.get("port_id"))

                if device not in failures:
                    failures[device] = []

                failures[device].append(port_label)

            top_5 = sorted(
                failures.items(),
                key=lambda x: len(x[1]),
                reverse=True
            )[:5]

            return [
                {
                    "device": device,
                    "fail_count": len(ports),
                    "ports": ports
                }
                for device, ports in top_5
            ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

async def save_failures_data():
    """Función async para guardar datos de fallas, manteniendo solo un registro en la tabla"""
    try:
        print("Extrayendo datos de la ruta de top failures")
        # Obtener datos de la API
        failures_data = await get_top_failures()
        print("HECHo")
        
        # Verificar y limpiar registros existentes
        existing = supabase.table("ports_failures").select("*").execute()
        if len(existing.data) > 0:
            # Eliminar todos los registros existentes
            supabase.table("ports_failures").delete().neq("id", "").execute()
        
        print("Insertando los datos a la BD")

        # Insertar el nuevo registro
        result = supabase.table("ports_failures").insert({
            "response": failures_data
        }).execute()
        
        print("Datos insertados correctamente a la BD")

        return {
            "message": "Failures data stored successfully",
            "id": result.data[0]["id"]
        }
    except Exception as e:
        print(f"Error saving failures data: {str(e)}")
        raise

@router.get(
    "/ports/failures_db",
    summary="Get stored port failures data from Supabase",
    description="Retrieves the latest port failures data stored in Supabase database",
    tags=["Ports DB"],
    response_model=list  # Ajusta según la estructura real de tus datos
)
async def get_failures_from_db():
    try:
        # Obtener el único registro de la tabla ports_failures
        response = supabase.table("ports_failures").select("response").execute()
        
        if not response.data:
            raise HTTPException(status_code=404, detail="No failures data found in database")
        
        # Retornar directamente el contenido del campo response
        return response.data[0]["response"]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

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