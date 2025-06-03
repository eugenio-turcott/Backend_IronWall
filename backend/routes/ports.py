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
            print(response.json())
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
    
    

