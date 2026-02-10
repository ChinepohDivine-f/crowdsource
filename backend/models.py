from sqlalchemy import Column, Integer, String, DateTime, BigInteger, Float, ForeignKey, Boolean, Enum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from geoalchemy2 import Geography
from database import Base
import uuid
import enum

class UserRole(str, enum.Enum):
    USER = "USER"
    ADMIN = "ADMIN"

class User(Base):
    __tablename__ = "core_user"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    role = Column(Enum(UserRole), default=UserRole.USER)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    devices = relationship("DeviceProfile", back_populates="user")
    measurements = relationship("NetworkMeasurement", back_populates="user")

class DeviceProfile(Base):
    __tablename__ = "core_device"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    api_key = Column(String, unique=True, index=True) # SRS Security Token
    user_id = Column(String, ForeignKey("core_user.id"), nullable=True) # Link to User
    manufacturer = Column(String, nullable=True)
    model = Column(String, nullable=True)
    os_version = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="devices")
    measurements = relationship("NetworkMeasurement", back_populates="device")

class NetworkMeasurement(Base):
    __tablename__ = "core_networkmeasurement"

    id = Column(Integer, primary_key=True, index=True)
    device_id = Column(String, ForeignKey("core_device.id"), index=True, nullable=True)
    user_id = Column(String, ForeignKey("core_user.id"), index=True, nullable=True) # Link to User
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

    device = relationship("DeviceProfile", back_populates="measurements")
    user = relationship("User", back_populates="measurements")
