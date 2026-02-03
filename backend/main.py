from fastapi import FastAPI, Depends, HTTPException
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import List
from geoalchemy2.shape import to_shape 
from shapely.geometry import Point

import models, schemas, database

# Create tables
models.Base.metadata.create_all(bind=database.engine)

app = FastAPI(title="Crowdsensed Drive Test API")

@app.get("/", response_class=HTMLResponse)
def read_root(db: Session = Depends(database.get_db)):
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Crowdsensed Drive Test - Web Dashboard</title>
        <meta charset="utf-8" />
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600&display=swap" rel="stylesheet">
        <style>
            body { font-family: 'Inter', sans-serif; margin: 0; padding: 0; background: #121212; color: white; }
            #map { height: 100vh; width: 100%; }
            .legend { 
                background: rgba(0,0,0,0.8); padding: 10px; border-radius: 5px; 
                line-height: 1.5; font-size: 12px; border: 1px solid #444;
            }
            .legend i { width: 12px; height: 12px; float: left; margin-right: 8px; border-radius: 50%; }
            .header-overlay {
                position: absolute; top: 10px; left: 50px; z-index: 1000;
                background: rgba(0,0,0,0.7); padding: 10px 20px; border-radius: 10px;
                backdrop-filter: blur(5px); border: 1px solid rgba(255,255,255,0.1);
            }
            h1 { margin: 0; font-size: 18px; color: #4facfe; }
            .btn { 
                display: inline-block; padding: 5px 10px; background: #4facfe; 
                color: white; text-decoration: none; border-radius: 5px; 
                font-size: 12px; margin-top: 5px;
            }
        </style>
    </head>
    <body>
        <div class="header-overlay">
            <h1>📡 Crowdsensed Drive Test Dashboard</h1>
            <div id="stats" style="font-size: 12px; color: #aaa;">Loading data...</div>
            <a href="/view/data" class="btn">View Raw Data Table</a>
        </div>
        <div id="map"></div>

        <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
        <script>
            var map = L.map('map').setView([0, 0], 2);
            L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
                attribution: '© OpenStreetMap contributors'
            }).addTo(map);

            var markers = L.featureGroup();

            fetch('/measurements/')
                .then(response => response.json())
                .then(data => {
                    document.getElementById('stats').innerText = `Total Records: ${data.length}`;
                    if (data.length === 0) {
                        document.getElementById('stats').innerText += " (No data synced yet)";
                        return;
                    }
                    data.forEach(m => {
                        var color = m.rsrp < -110 ? '#ff4b2b' : '#00f2fe';
                        var marker = L.circleMarker([m.latitude, m.longitude], {
                            radius: 8,
                            fillColor: color,
                            color: "#fff",
                            weight: 1,
                            opacity: 1,
                            fillOpacity: 0.8
                        }).bindPopup(`
                            <strong>Device: ${m.device_id}</strong><br>
                            Time: ${new Date(m.timestamp).toLocaleString()}<br>
                            Network: ${m.network_type}<br>
                            RSRP: ${m.rsrp} dBm<br>
                            RSRQ: ${m.rsrq} dB<br>
                            RSSI: ${m.rssi} dBm<br>
                            SINR: ${m.sinr} dB<br>
                            Status: ${m.status}<br>
                            Cell ID: ${m.cell_id}
                        `);
                        markers.addLayer(marker);
                    });
                    markers.addTo(map);
                    map.fitBounds(markers.getBounds(), {padding: [50, 50]});
                });

            var legend = L.control({position: 'bottomright'});
            legend.onAdd = function (map) {
                var div = L.DomUtil.create('div', 'legend');
                div.innerHTML += '<i style="background: #00f2fe"></i> Good Signal<br>';
                div.innerHTML += '<i style="background: #ff4b2b"></i> Coverage Hole<br>';
                return div;
            };
            legend.addTo(map);
        </script>
    </body>
    </html>
    """
    return html_content

@app.get("/view/data", response_class=HTMLResponse)
def view_data(db: Session = Depends(database.get_db)):
    # Fetch all records
    measurements = db.query(models.Measurement).order_by(models.Measurement.timestamp.desc()).all()
    
    rows = ""
    for m in measurements:
        pt = to_shape(m.location)
        rows += f"""
        <tr>
            <td>{m.id}</td>
            <td>{m.timestamp}</td>
            <td>{m.device_id}</td>
            <td>{m.network_type}</td>
            <td>{m.rsrp}</td>
            <td>{m.rsrq}</td>
            <td>{m.rssi}</td>
            <td>{m.sinr}</td>
            <td>{m.status}</td>
            <td>{pt.y:.5f}, {pt.x:.5f}</td>
        </tr>
        """
    
    html = f"""
    <html>
    <head>
        <title>Raw Data View</title>
        <style>
            body {{ font-family: sans-serif; padding: 20px; background: #f4f4f9; }}
            table {{ width: 100%; border-collapse: collapse; background: white; }}
            th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
            th {{ background: #4facfe; color: white; }}
            tr:nth-child(even) {{ background: #f9f9f9; }}
            .back {{ margin-bottom: 20px; display: inline-block; text-decoration: none; color: #4facfe; font-weight: bold; }}
        </style>
    </head>
    <body>
        <a href="/" class="back">← Back to Map Dashboard</a>
        <h1>🗄️ Raw Measurement Database</h1>
        <p>Total Records: {len(measurements)}</p>
        <table>
            <thead>
                <tr>
                    <th>ID</th>
                    <th>Timestamp</th>
                    <th>Device</th>
                    <th>Type</th>
                    <th>RSRP</th>
                    <th>RSRQ</th>
                    <th>RSSI</th>
                    <th>SINR</th>
                    <th>Status</th>
                    <th>Coordinates (Lat, Lon)</th>
                </tr>
            </thead>
            <tbody>
                {rows}
            </tbody>
        </table>
    </body>
    </html>
    """
    return html

@app.post("/measurements/", response_model=List[schemas.MeasurementResponse])
def create_measurements(measurements: List[schemas.MeasurementCreate], db: Session = Depends(database.get_db)):
    print(f"📡 Received {len(measurements)} measurements from mobile app.")
    db_measurements = []
    for m in measurements:
        point_wkt = f"POINT({m.longitude} {m.latitude})"
        db_measurement = models.Measurement(
            device_id=m.device_id,
            network_type=m.network_type,
            rsrp=m.rsrp,
            rsrq=m.rsrq,
            rssi=m.rssi,
            sinr=m.sinr,
            cell_id=m.cell_id,
            status=m.status,
            location=point_wkt,
            timestamp=m.timestamp
        )
        db.add(db_measurement)
        db_measurements.append(db_measurement)
    
    db.commit()
    for m in db_measurements:
        db.refresh(m)
        
    response = []
    for m in db_measurements:
        pt = to_shape(m.location)
        response.append(schemas.MeasurementResponse(
            id=m.id,
            device_id=m.device_id,
            network_type=m.network_type,
            rsrp=m.rsrp,
            rsrq=m.rsrq,
            rssi=m.rssi,
            sinr=m.sinr,
            cell_id=m.cell_id,
            status=m.status,
            latitude=pt.y,
            longitude=pt.x,
            timestamp=m.timestamp
        ))
    return response

@app.get("/measurements/", response_model=List[schemas.MeasurementResponse])
def get_measurements(db: Session = Depends(database.get_db)):
    measurements = db.query(models.Measurement).all()
    response = []
    for m in measurements:
        pt = to_shape(m.location)
        response.append(schemas.MeasurementResponse(
            id=m.id,
            device_id=m.device_id,
            network_type=m.network_type,
            rsrp=m.rsrp,
            rsrq=m.rsrq,
            rssi=m.rssi,
            sinr=m.sinr,
            cell_id=m.cell_id,
            status=m.status,
            latitude=pt.y,
            longitude=pt.x,
            timestamp=m.timestamp
        ))
    return response

@app.get("/analytics/coverage_holes")
def get_coverage_holes(db: Session = Depends(database.get_db)):
    holes = db.query(models.Measurement).filter(models.Measurement.rsrp < -110).all()
    result = []
    for h in holes:
        pt = to_shape(h.location)
        result.append({
            "lat": pt.y,
            "lon": pt.x,
            "rsrp": h.rsrp,
            "device": h.device_id,
            "time": h.timestamp
        })
    return {"count": len(holes), "holes": result}
