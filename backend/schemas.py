from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class MeasurementDetail(BaseModel):
    ts: int  # Unix timestamp from client
    lat: float
    lon: float
    acc: float
    net: str
    mcc: Optional[int] = None
    mnc: Optional[int] = None
    ci: Optional[int] = None
    metrics: dict  # Nested metrics: rsrp, rsrq, sinr, etc.

class BatchMeta(BaseModel):
    device_id: str
    batch_size: int
    client_timestamp: int
    manufacturer: Optional[str] = None
    model: Optional[str] = None
    os_version: Optional[str] = None

class BatchPayload(BaseModel):
    meta: BatchMeta
    data: List[MeasurementDetail]

class MeasurementResponse(BaseModel):
    id: int
    device_id: str
    network_type: str
    rsrp: int
    status: str
    latitude: float
    longitude: float
    timestamp: datetime

    class Config:
        from_attributes = True

# Security Models
class DeviceRegistration(BaseModel):
    device_id: str
    manufacturer: str
    model: str
    os_version: str

class RegistrationResponse(BaseModel):
    api_key: str
    message: str

# Auth Models
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: Optional[str] = None

class UserCreate(BaseModel):
    username: str
    email: str
    password: str

class UserResponse(BaseModel):
    id: str
    username: Optional[str] = None
    email: str
    role: str
    is_active: bool

    class Config:
        from_attributes = True
