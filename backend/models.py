from sqlalchemy import Column, Integer, String, DateTime, BigInteger, Float
from sqlalchemy.sql import func
from geoalchemy2 import Geography
from database import Base

class Measurement(Base):
    __tablename__ = "measurements"

    id = Column(Integer, primary_key=True, index=True)
    device_id = Column(String, index=True)
    network_type = Column(String)  # 'LTE' or 'NR'
    rsrp = Column(Integer)
    sinr = Column(Integer)
    cell_id = Column(BigInteger)
    # Stores location as a Geography point (WGS84)
    location = Column(Geography(geometry_type='POINT', srid=4326)) 
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
