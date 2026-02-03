from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class MeasurementBase(BaseModel):
    device_id: str
    network_type: str
    rsrp: int
    rsrq: int
    rssi: int
    sinr: int
    cell_id: int
    status: str
    latitude: float
    longitude: float
    timestamp: Optional[datetime] = None

class MeasurementCreate(MeasurementBase):
    pass

class MeasurementResponse(MeasurementBase):
    id: int
    
    class Config:
        from_attributes = True
