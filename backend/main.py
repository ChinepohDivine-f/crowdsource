from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import List
from geoalchemy2.shape import to_shape 
from shapely.geometry import Point

import models, schemas, database

# Create tables
models.Base.metadata.create_all(bind=database.engine)

app = FastAPI(title="Crowdsensed Drive Test API")

@app.get("/")
def read_root():
    return {"message": "Welcome to Crowdsensed Drive Test API"}

@app.post("/measurements/", response_model=List[schemas.MeasurementResponse])
def create_measurements(measurements: List[schemas.MeasurementCreate], db: Session = Depends(database.get_db)):
    db_measurements = []
    for m in measurements:
        # Create Point geometry: POINT(lon lat)
        point_wkt = f"POINT({m.longitude} {m.latitude})"
        
        db_measurement = models.Measurement(
            device_id=m.device_id,
            network_type=m.network_type,
            rsrp=m.rsrp,
            sinr=m.sinr,
            cell_id=m.cell_id,
            location=point_wkt,
            timestamp=m.timestamp
        )
        db.add(db_measurement)
        db_measurements.append(db_measurement)
    
    db.commit()
    # Refresh to get IDs and created timestamps
    for m in db_measurements:
        db.refresh(m)
        
    # Manual mapping for response since 'location' is a WKBElement
    response = []
    for m in db_measurements:
        # Convert WKB to shapely point to get lat/lon back if needed
        # But for response, we can just echo input or custom map. 
        # Here we just simpler return what we saved.
        pt = to_shape(m.location)
        response.append(schemas.MeasurementResponse(
            id=m.id,
            device_id=m.device_id,
            network_type=m.network_type,
            rsrp=m.rsrp,
            sinr=m.sinr,
            cell_id=m.cell_id,
            latitude=pt.y,
            longitude=pt.x,
            timestamp=m.timestamp
        ))
        
    return response

@app.get("/analytics/coverage_holes")
def get_coverage_holes(db: Session = Depends(database.get_db)):
    # Simple logic: RSRP < -110 dBm
    # We can stick to raw SQL for PostGIS power or use ORM
    
    # Let's find holes
    holes = db.query(models.Measurement).filter(models.Measurement.rsrp < -110).all()
    
    result = []
    for h in holes:
        pt = to_shape(h.location)
        result.append({
            "lat": pt.y,
            "lon": pt.x,
            "rsrp": h.rsrp
        })
    return {"count": len(holes), "holes": result}
