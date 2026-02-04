from sqlalchemy import Column, Integer, String, DateTime, BigInteger, Float, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from geoalchemy2 import Geography
from database import Base
import uuid

class DeviceProfile(Base):
    __tablename__ = "core_device"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    api_key = Column(String, unique=True, index=True) # SRS Security Token
    manufacturer = Column(String, nullable=True)
    model = Column(String, nullable=True)
    os_version = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class NetworkMeasurement(Base):
    __tablename__ = "core_networkmeasurement"

    id = Column(Integer, primary_key=True, index=True)
    device_id = Column(String, ForeignKey("core_device.id"), index=True)
    network_type = Column(String)  # 'LTE' or 'NR'
    rsrp = Column(Integer)
    rsrq = Column(Integer)
    rssi = Column(Integer)
    sinr = Column(Float) # SRS says Float
    cell_id = Column(BigInteger)
    status = Column(String)  # 'Good' or 'Hole'
    # Stores location as a Geography point (WGS84)
    location = Column(Geography(geometry_type='POINT', srid=4326)) 
    recorded_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    device = relationship("DeviceProfile")
