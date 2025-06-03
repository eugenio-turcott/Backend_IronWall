from fastapi import APIRouter, HTTPException, Query
from typing import List
import httpx
import os
from dotenv import load_dotenv

load_dotenv() 
OBSERVIUM_API_BASE = os.getenv("API_URL")
OBS_USER = os.getenv("API_USERNAME")
OBS_PASS = os.getenv("API_PASSWORD")

router = APIRouter()

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
                        device_names.append({"ip": ip, "error": "No device found"})
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
