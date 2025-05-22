from pydantic import BaseModel
from typing import Optional


class LoginRequest(BaseModel):
    email: str
    password: str



class DeviceInfo(BaseModel):
    hostname: Optional[str]
    ip: Optional[str]
    location: Optional[str]
    location_id: Optional[str]
    location_lat: Optional[str]
    location_lon: Optional[str]
    sysName: Optional[str]
    os: Optional[str]
    vendor: Optional[str]
    type: Optional[str]
    status: Optional[str]

class Alert(BaseModel):
    alert_table_id: Optional[str]
    device_id: Optional[str]
    last_ok: Optional[str]
    severity: Optional[str]
    status: Optional[str]
    recovered: Optional[str]
    device: Optional[DeviceInfo] 

