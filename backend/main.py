from fastapi import FastAPI, Depends, HTTPException, status, Request, Header, Security
from fastapi.responses import HTMLResponse
from fastapi.security import APIKeyHeader
from sqlalchemy.orm import Session
from sqlalchemy import text, func
from typing import List, Optional
from geoalchemy2.shape import to_shape 
from shapely.geometry import Point, mapping
from datetime import datetime
import secrets
import json

# Rate Limiting
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

import models, schemas, database, analysis, auth
from routers import auth as auth_router

# Create tables
models.Base.metadata.create_all(bind=database.engine)

# Security Setup
limiter = Limiter(key_func=get_remote_address)
app = FastAPI(title="Senzor API", version="1.0")
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

# Include Auth Router
app.include_router(auth_router.router)

API_KEY_NAME = "Authorization"
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)

# --- NAVIGATION & UI COMPONENTS ---
NAV_HTML = """
<nav style="background: #1e1e1e; padding: 15px; border-bottom: 1px solid #333;">
    <div style="max-width: 1200px; margin: 0 auto; display: flex; justify-content: space-between; align-items: center;">
        <div style="font-weight: bold; font-size: 18px; color: #4facfe;">
            📡 Senzor <span style="font-size: 12px; color: #666; font-weight: normal;">Admin Panel</span>
        </div>
        <div>
            <a href="/" style="color: #ccc; text-decoration: none; margin-left: 20px; font-size: 14px;">Dashboard</a>
            <a href="/view/register" style="color: #ccc; text-decoration: none; margin-left: 20px; font-size: 14px;">Register Device</a>
            <a href="/view/analytics" style="color: #ccc; text-decoration: none; margin-left: 20px; font-size: 14px;">Analytics</a>
            <a href="/view/simulate" style="color: #ccc; text-decoration: none; margin-left: 20px; font-size: 14px;">Simulator</a>
            <a href="/view/data" style="color: #ccc; text-decoration: none; margin-left: 20px; font-size: 14px;">Raw Data</a>
            <a href="/docs" target="_blank" style="color: #4facfe; text-decoration: none; margin-left: 20px; font-size: 14px;">API Docs ↗</a>
        </div>
    </div>
</nav>
"""

BASE_STYLE = """
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600&display=swap" rel="stylesheet">
<style>
    body { font-family: 'Inter', sans-serif; margin: 0; padding: 0; background: #121212; color: #e0e0e0; }
    .container { max-width: 1000px; margin: 40px auto; padding: 20px; }
    h1 { color: #fff; border-bottom: 2px solid #4facfe; padding-bottom: 10px; margin-bottom: 30px; display: inline-block; }
    .card { background: #1e1e1e; padding: 25px; border-radius: 12px; border: 1px solid #333; margin-bottom: 20px; box-shadow: 0 4px 20px rgba(0,0,0,0.3); }
    .stats-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin-bottom: 30px; }
    .stat-card { background: linear-gradient(135deg, #1e1e1e 0%, #252525 100%); padding: 20px; border-radius: 12px; border: 1px solid #333; text-align: center; transition: transform 0.3s ease, border-color 0.3s ease; }
    .stat-card:hover { transform: translateY(-5px); border-color: #4facfe; }
    .stat-value { font-size: 28px; font-weight: bold; color: #4facfe; margin-bottom: 5px; }
    .stat-label { font-size: 12px; color: #888; text-transform: uppercase; letter-spacing: 1px; }
    @keyframes pulse { 0% { box-shadow: 0 0 0 0 rgba(79, 172, 254, 0.4); } 70% { box-shadow: 0 0 0 10px rgba(79, 172, 254, 0); } 100% { box-shadow: 0 0 0 0 rgba(79, 172, 254, 0); } }
    .pulse-ready { animation: pulse 2s infinite; }
    label { display: block; margin-bottom: 8px; font-weight: 600; color: #aaa; font-size: 12px; text-transform: uppercase; }
    input, select, textarea { width: 100%; padding: 10px; background: #2d2d2d; border: 1px solid #444; color: white; border-radius: 4px; margin-bottom: 20px; box-sizing: border-box; }
    button { padding: 10px 20px; background: #4facfe; color: white; border: none; border-radius: 4px; cursor: pointer; font-weight: 600; }
    button:hover { background: #00f2fe; color: #000; }
    button.secondary { background: #333; color: #ccc; }
    .success { padding: 15px; background: rgba(0, 255, 0, 0.1); border: 1px solid #00ff00; color: #00ff00; border-radius: 4px; display: none; margin-bottom: 20px; }
    .error { padding: 15px; background: rgba(255, 0, 0, 0.1); border: 1px solid #ff0000; color: #ff0000; border-radius: 4px; display: none; margin-bottom: 20px; }
    pre { background: #000; padding: 15px; border-radius: 4px; overflow-x: auto; color: #00ff00; font-family: monospace; }
</style>
"""

# --- AUTH & HELPERS ---
async def get_api_key(api_key_header: str = Security(api_key_header), db: Session = Depends(database.get_db)):
    # Fallback to check for Bearer token for User-based ingestion in the future
    if not api_key_header:
        raise HTTPException(status_code=401, detail="Missing Authorization Header")
    
    # Simple check: is it a Token (Device) or Bearer (User)?
    # For this function, we primarily look for Device API Key 'Token <key>'
    try:
        scheme, token = api_key_header.split()
        if scheme.lower() == 'bearer':
            # This would be a user, logic handled by auth.get_current_user
            # For now, this dependency is strictly for legacy Device API Key
             raise HTTPException(status_code=401, detail="Device Auth requires 'Token' scheme")
        if scheme.lower() != 'token': 
            raise HTTPException(status_code=401, detail="Invalid Scheme")
    except:
        raise HTTPException(status_code=401, detail="Invalid Header Format")

    device = db.query(models.DeviceProfile).filter(models.DeviceProfile.api_key == token).first()
    if not device:
        raise HTTPException(status_code=403, detail="Invalid API Key")
    return device


# --- UI ROUTES ---

@app.get("/", response_class=HTMLResponse)
def read_root():
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Senzor Dashboard</title>
        <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
        {BASE_STYLE}
        <style>
            #map {{ height: calc(100vh - 54px); width: 100%; }}
            .legend {{ background: rgba(0,0,0,0.8); padding: 10px; border-radius: 5px; border: 1px solid #444; color: #fff; font-size: 12px; }}
            .legend i {{ width: 12px; height: 12px; float: left; margin-right: 8px; border-radius: 50%; }}
        </style>
    </head>
    <body>
        {NAV_HTML}
        <div id="map"></div>
        <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
        <script>
            var map = L.map('map').setView([0, 0], 2);
            L.tileLayer('https://{{s}}.tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png', {{ attribution: '© OpenStreetMap' }}).addTo(map);
            
            var markersLayer = L.featureGroup();
            var holesLayer = L.featureGroup();
            var heatmapLayer = L.featureGroup();

            fetch('/api/v1/measurements/').then(r => r.json()).then(data => {{
                data.forEach(m => {{
                    var color = m.rsrp < -110 ? '#ff4b2b' : '#00f2fe';
                    L.circleMarker([m.latitude, m.longitude], {{ radius: 6, fillColor: color, color: "#fff", weight: 1, fillOpacity: 0.8 }})
                    .bindPopup(`Device: ${{m.device_id}}<br>RSRP: ${{m.rsrp}} dBm`).addTo(markersLayer);
                }});
                markersLayer.addTo(map);
                if(data.length > 0) map.fitBounds(markersLayer.getBounds());
            }});
            
            // Auto-load Heatmap
            fetch('/api/v1/analytics/heatmap').then(r => r.json()).then(data => {{
                data.forEach(d => {{
                    var color = d.val < -110 ? '#ff0000' : (d.val < -90 ? '#ffff00' : '#00ff00');
                    var bounds = [[d.lat - 0.0005, d.lon - 0.0005], [d.lat + 0.0005, d.lon + 0.0005]];
                    L.rectangle(bounds, {{ color: color, weight: 0, fillOpacity: 0.4 }}).addTo(heatmapLayer);
                }});
            }});

            var overlays = {{ "Raw Points": markersLayer, "Signal Heatmap": heatmapLayer, "Coverage Holes": holesLayer }};
            L.control.layers(null, overlays, {{collapsed: false}}).addTo(map);
        </script>
    </body>
    </html>
    """

@app.get("/view/register", response_class=HTMLResponse)
def view_register():
    return f"""
    <!DOCTYPE html>
    <html>
    <head><title>Register Device</title>{BASE_STYLE}</head>
    <body>
        {NAV_HTML}
        <div class="container">
            <h1>📝 Register New Device</h1>
            <div class="card">
                <div id="msg" class="success"></div>
                <div id="err" class="error"></div>
                
                <form id="regForm" onsubmit="register(event)">
                    <label>Device ID (Unique UUID/Serial)</label>
                    <input type="text" id="device_id" value="test-device-01" required>
                    
                    <label>Manufacturer</label>
                    <input type="text" id="manufacturer" value="Generic" required>
                    
                    <label>Model</label>
                    <input type="text" id="model" value="Simulator v1" required>
                    
                    <label>OS Version</label>
                    <input type="text" id="os_version" value="Android 14">
                    
                    <button type="submit">Generate API Key</button>
                </form>
            </div>
            
            <div class="card" id="resultCard" style="display:none;">
                <label>✅ Registration Successful</label>
                <p>Save this API Key securely. It is required for all data uploads.</p>
                <pre id="apiKeyBox"></pre>
            </div>
        </div>
        <script>
            async function register(e) {{
                e.preventDefault();
                const payload = {{
                    device_id: document.getElementById('device_id').value,
                    manufacturer: document.getElementById('manufacturer').value,
                    model: document.getElementById('model').value,
                    os_version: document.getElementById('os_version').value
                }};
                
                try {{
                    const res = await fetch('/api/v1/register', {{
                        method: 'POST',
                        headers: {{'Content-Type': 'application/json'}},
                        body: JSON.stringify(payload)
                    }});
                    const data = await res.json();
                    
                    if(res.ok) {{
                        document.getElementById('msg').innerText = data.message;
                        document.getElementById('msg').style.display = 'block';
                        document.getElementById('apiKeyBox').innerText = data.api_key;
                        document.getElementById('resultCard').style.display = 'block';
                        localStorage.setItem('senzor_api_key', data.api_key); // Save for simulator
                        localStorage.setItem('senzor_device_id', payload.device_id);
                    }} else {{
                        document.getElementById('err').innerText = data.detail || 'Error';
                        document.getElementById('err').style.display = 'block';
                    }}
                }} catch(err) {{ alert(err); }}
            }}
        </script>
    </body>
    </html>
    """

@app.get("/view/analytics", response_class=HTMLResponse)
def view_analytics(db: Session = Depends(database.get_db)):
    try:
        # Quick aggregation for stat cards
        total_count = db.query(models.NetworkMeasurement).count()
        avg_rsrp = db.query(func.avg(models.NetworkMeasurement.rsrp)).scalar() or 0
        unique_devices = db.query(models.NetworkMeasurement.device_id).distinct().count()
    except Exception as e:
        print(f"DB Error: {e}")
        return HTMLResponse(f"<h1>Database Connection Error</h1><p>Could not connect to Supabase. Check DATABASE_URL.</p><pre>{e}</pre>", status_code=500)
    
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Senzor Analytics</title>
        {BASE_STYLE}
        <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    </head>
    <body>
        {NAV_HTML}
        <div class="container">
            <h1>📊 Network Intelligence Dashboard</h1>
            
            <div class="stats-grid">
                <div class="stat-card">
                    <div class="stat-value">{total_count}</div>
                    <div class="stat-label">Total Data Points</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value">{avg_rsrp:.1f} dBm</div>
                    <div class="stat-label">Avg Signal (RSRP)</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value">{unique_devices}</div>
                    <div class="stat-label">Active Devices</div>
                </div>
            </div>

            <div style="display: grid; grid-template-columns: 2fr 1fr; gap: 20px;">
                <div class="card">
                    <h3>📡 Signal Strength Distribution</h3>
                    <canvas id="rsrpChart" height="150"></canvas>
                </div>
                <div class="card">
                    <h3>📶 Network Technology</h3>
                    <canvas id="netTypeChart"></canvas>
                </div>
            </div>

            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-top:20px;">
                <div class="card">
                    <h3>🧠 ML Signal Predictor</h3>
                    <p style="color: #888; font-size: 13px;">Predict coverage quality at any coordinate using our RandomForest spatial model.</p>
                    <div style="margin-top: 20px;">
                        <input type="text" id="ml_lat" placeholder="Latitude (e.g. 40.7128)">
                        <input type="text" id="ml_lon" placeholder="Longitude (e.g. -74.0060)">
                        <button onclick="predictSignal()" style="width: 100%;">📊 Forecast Signal</button>
                    </div>
                    <div id="mlResult" class="pulse-ready" style="margin-top: 20px; display:none; padding: 15px; border-radius: 8px; text-align: center; border: 1px solid #4facfe;">
                        <div style="font-size: 12px; color: #888;">PREDICTED RSRP</div>
                        <div id="mlVal" style="font-size: 32px; font-weight: bold; color: #4facfe;">-105.4 dBm</div>
                    </div>
                </div>

                <div class="card">
                    <h3>🛠 Spatial Clustering (DBSCAN)</h3>
                    <p style="color: #888; font-size: 13px;">Detect contiguous "Coverage Holes" automatically from raw measurement density.</p>
                    <button class="secondary" onclick="runAnalysis()" style="width:100%; margin-top: 15px;">Run Hole Detection</button>
                    <div id="analyticsResult" style="margin-top: 20px; display:none;">
                        <pre id="jsonOutput" style="font-size: 10px; max-height: 150px;"></pre>
                    </div>
                </div>
            </div>
        </div>

        <script>
            // Fetch Stats and Load Charts
            async function loadCharts() {{
                const res = await fetch('/api/v1/analytics/stats');
                const data = await res.json();

                // RSRP Chart
                new Chart(document.getElementById('rsrpChart'), {{
                    type: 'bar',
                    data: {{
                        labels: data.rsrp_bins.map(b => b.range),
                        datasets: [{{
                            label: 'Measurement Count',
                            data: data.rsrp_bins.map(b => b.count),
                            backgroundColor: '#4facfe88',
                            borderColor: '#4facfe',
                            borderWidth: 1
                        }}]
                    }},
                    options: {{ responsive: true, scales: {{ y: {{ beginAtZero: true, grid: {{ color: '#333' }} }}, x: {{ grid: {{ display: false }} }} }} }}
                }});

                // Network Type Chart
                new Chart(document.getElementById('netTypeChart'), {{
                    type: 'doughnut',
                    data: {{
                        labels: Object.keys(data.net_types),
                        datasets: [{{
                            data: Object.values(data.net_types),
                            backgroundColor: ['#4facfe', '#00f2fe', '#333']
                        }}]
                    }},
                    options: {{ responsive: true, plugins: {{ legend: {{ position: 'bottom' }} }} }}
                }});
            }}

            async function predictSignal() {{
                const lat = document.getElementById('ml_lat').value;
                const lon = document.getElementById('ml_lon').value;
                const res = await fetch(`/api/v1/analytics/predict?lat=${{lat}}&lon=${{lon}}`);
                const data = await res.json();
                
                const box = document.getElementById('mlResult');
                const val = document.getElementById('mlVal');
                box.style.display = 'block';
                if(data.prediction) {{
                    val.innerText = data.prediction.toFixed(1) + " dBm";
                    val.style.color = data.prediction < -110 ? '#ff4b2b' : '#4facfe';
                }} else {{
                    val.innerText = "Sparse Data";
                    val.style.color = "#888";
                }}
            }}

            async function runAnalysis() {{
                const res = await fetch('/api/v1/analytics/trigger');
                const data = await res.json();
                document.getElementById('jsonOutput').innerText = JSON.stringify(data, null, 2);
                document.getElementById('analyticsResult').style.display = 'block';
            }}

            loadCharts();
        </script>
    </body>
    </html>
    """

@app.get("/view/simulate", response_class=HTMLResponse)
def view_simulate():
    return f"""
    <!DOCTYPE html>
    <html>
    <head><title>Device Simulator</title>{BASE_STYLE}</head>
    <body>
        {NAV_HTML}
        <div class="container">
            <h1>🚀 Drive Test Simulator</h1>
            <div class="card">
                <p>Simulate a device driving along a route and uploading batch data.</p>
                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px;">
                    <div>
                        <label>Auth Token</label>
                        <input id="token" type="password" placeholder="Paste API Key here">
                    </div>
                    <div>
                        <label>Device ID</label>
                        <input id="devId" type="text" placeholder="Device UUID">
                    </div>
                </div>
                <button onclick="simulateUpload()">🚀 Send Batch (10 Points)</button>
            </div>
            <div id="simLog" class="card" style="font-family: monospace; font-size: 12px; height: 300px; overflow-y: scroll; display:none;"></div>
        </div>
        <script>
            // Auto-fill from previous registration
            document.getElementById('token').value = localStorage.getItem('senzor_api_key') || '';
            document.getElementById('devId').value = localStorage.getItem('senzor_device_id') || '';
            
            function log(msg) {{
                const div = document.getElementById('simLog');
                div.style.display = 'block';
                div.innerHTML += `<div>[${{new Date().toLocaleTimeString()}}] ${{msg}}</div>`;
                div.scrollTop = div.scrollHeight;
            }}

            async function simulateUpload() {{
                const token = document.getElementById('token').value;
                const devId = document.getElementById('devId').value;
                if(!token) return alert("Please Register first to get an API Token!");
                
                // Generate fake path
                const baseLat = 40.7128; // NYC
                const baseLon = -74.0060;
                const data = [];
                const now = Math.floor(Date.now() / 1000);
                
                for(let i=0; i<10; i++) {{
                    data.push({{
                        ts: now - i*5,
                        lat: baseLat + (Math.random() * 0.01),
                        lon: baseLon + (Math.random() * 0.01),
                        acc: 5.0,
                        net: Math.random() > 0.5 ? 'LTE' : 'NR',
                        ci: 12345,
                        metrics: {{
                            rsrp: -80 - Math.floor(Math.random() * 50), // Random -80 to -130
                            rsrq: -10, sinr: 15
                        }}
                    }});
                }}
                
                const payload = {{
                    meta: {{
                        device_id: devId,
                        batch_size: 10,
                        client_timestamp: now,
                        model: "WebSimulator",
                        os_version: "Web 1.0"
                    }},
                    data: data
                }};
                
                log("📡 Uploading batch...");
                try {{
                    const res = await fetch('/api/v1/ingest/batch', {{
                        method: 'POST',
                        headers: {{
                            'Content-Type': 'application/json',
                            'Authorization': 'Token ' + token
                        }},
                        body: JSON.stringify(payload)
                    }});
                    const json = await res.json();
                    if(res.ok) log("✅ Success: " + json.message);
                    else log("❌ Error: " + (json.detail || res.statusText));
                }} catch(e) {{ log("🧨 Network Error"); }}
            }}
        </script>
    </body>
    </html>
    """

@app.get("/view/data", response_class=HTMLResponse)
def view_data(db: Session = Depends(database.get_db)):
    measurements = db.query(models.NetworkMeasurement).order_by(models.NetworkMeasurement.recorded_at.desc()).limit(100).all()
    rows = ""
    for m in measurements:
        pt = to_shape(m.location)
        status_color = "#ff4b2b" if m.status == "Hole" else "#00f2fe";
        rows += f"""
        <tr style="border-bottom: 1px solid #333;">
            <td style="padding: 10px;">{m.id}</td>
            <td style="padding: 10px;">{m.recorded_at.strftime('%Y-%m-%d %H:%M:%S')}</td>
            <td style="padding: 10px;">{m.device_id[:8]}...</td>
            <td style="padding: 10px;">{m.network_type}</td>
            <td style="padding: 10px; font-weight: bold;">{m.rsrp}</td>
            <td style="padding: 10px;"><span style="color:{status_color}">{m.status}</span></td>
            <td style="padding: 10px;">{pt.y:.4f}, {pt.x:.4f}</td>
        </tr>
        """
    return f"""
    <!DOCTYPE html>
    <html>
    <head><title>Raw Data</title>{BASE_STYLE}</head>
    <body>
        {NAV_HTML}
        <div class="container">
            <h1>🗄️ Measurement Database (Last 100)</h1>
            <div class="card" style="padding: 0; overflow: hidden;">
                <table style="width: 100%; border-collapse: collapse; text-align: left;">
                    <thead style="background: #2d2d2d; color: #aaa; text-transform: uppercase; font-size: 12px;">
                        <tr>
                            <th style="padding: 15px;">ID</th>
                            <th>Time</th>
                            <th>Device</th>
                            <th>Net</th>
                            <th>RSRP</th>
                            <th>Status</th>
                            <th>Location</th>
                        </tr>
                    </thead>
                    <tbody style="color: #ddd;">
                        {rows}
                    </tbody>
                </table>
            </div>
        </div>
    </body>
    </html>
    """

# --- API ENDPOINTS (Logic) ---

@app.post("/api/v1/register", response_model=schemas.RegistrationResponse)
@limiter.limit("5/minute") 
def register_device(request: Request, payload: schemas.DeviceRegistration, db: Session = Depends(database.get_db)):
    device = db.query(models.DeviceProfile).filter(models.DeviceProfile.id == payload.device_id).first()
    token = secrets.token_hex(32)
    
    if device:
        device.api_key = token
        device.manufacturer = payload.manufacturer
        device.model = payload.model
        device.os_version = payload.os_version
        msg = "Device updated. New token issued."
    else:
        device = models.DeviceProfile(
            id=payload.device_id,
            manufacturer=payload.manufacturer,
            model=payload.model,
            os_version=payload.os_version,
            api_key=token
        )
        db.add(device)
        msg = "Device registered successfully."
    
    db.commit()
    return {"api_key": token, "message": msg}

@app.post("/api/v1/ingest/batch", status_code=status.HTTP_201_CREATED)
def ingest_batch(payload: schemas.BatchPayload, device: models.DeviceProfile = Depends(get_api_key), db: Session = Depends(database.get_db)):
    if payload.meta.device_id != device.id:
        pass # Allow for simulator mismatch for now, or log warning
    
    measurements = []
    for item in payload.data:
        recorded_at = datetime.fromtimestamp(item.ts)
        rsrp = item.metrics.get("rsrp", -140)
        status_val = "Hole" if rsrp < -110 else "Good"
        
        measurement = models.NetworkMeasurement(
            device_id=device.id,
            network_type=item.net,
            rsrp=rsrp,
            rsrq=item.metrics.get("rsrq"),
            rssi=item.metrics.get("rssi"),
            sinr=item.metrics.get("sinr"),
            cell_id=item.ci,
            status=status_val,
            location=f"POINT({item.lon} {item.lat})",
            recorded_at=recorded_at
        )
        db.add(measurement)
        measurements.append(measurement)
        
    db.commit()
    return {"message": "Batch processed successfully", "saved_count": len(measurements)}

@app.get("/api/v1/measurements/", response_model=List[schemas.MeasurementResponse])
def get_measurements(db: Session = Depends(database.get_db)):
    measurements = db.query(models.NetworkMeasurement).order_by(models.NetworkMeasurement.recorded_at.desc()).limit(1000).all()
    response = []
    for m in measurements:
        pt = to_shape(m.location)
        response.append(schemas.MeasurementResponse(
            id=m.id,
            device_id=m.device_id,
            network_type=m.network_type,
            rsrp=m.rsrp,
            rsrq=m.rsrq or 0,
            rssi=m.rssi or 0,
            sinr=int(m.sinr) if m.sinr is not None else 0,
            cell_id=m.cell_id or 0,
            status=m.status,
            latitude=pt.y,
            longitude=pt.x,
            timestamp=m.recorded_at
        ))
    return response

@app.get("/api/v1/analytics/trigger")
def trigger_analysis(db: Session = Depends(database.get_db)):
    holes = analysis.detect_coverage_holes(db)
    features = []
    for h in holes:
        features.append({
            "type": "Feature",
            "properties": {
                "severity": h["severity"],
                "count": h["count"]
            },
            "geometry": mapping(h["geometry"])
        })
    return {"type": "FeatureCollection", "features": features}

@app.get("/api/v1/analytics/stats")
def get_analytics_stats(db: Session = Depends(database.get_db)):
    # RSRP Distribution
    sql = "SELECT rsrp FROM core_networkmeasurement"
    rsrps = [r[0] for r in db.execute(text(sql)).fetchall()]
    
    bins = [
        {"range": "< -120", "count": 0},
        {"range": "-120 to -110", "count": 0},
        {"range": "-110 to -100", "count": 0},
        {"range": "-100 to -90", "count": 0},
        {"range": "> -90", "count": 0}
    ]
    for r in rsrps:
        if r < -120: bins[0]["count"] += 1
        elif r < -110: bins[1]["count"] += 1
        elif r < -100: bins[2]["count"] += 1
        elif r < -90: bins[3]["count"] += 1
        else: bins[4]["count"] += 1
        
    # Network Type Mix
    net_sql = "SELECT network_type, COUNT(*) FROM core_networkmeasurement GROUP BY network_type"
    net_types = dict(db.execute(text(net_sql)).fetchall())
    
    return {"rsrp_bins": bins, "net_types": net_types}

@app.get("/api/v1/analytics/predict")
def get_ml_prediction(lat: float, lon: float, db: Session = Depends(database.get_db)):
    prediction = analysis.predict_signal_strength(db, lat, lon)
    return {"prediction": prediction}

@app.get("/api/v1/analytics/heatmap")
def get_heatmap(db: Session = Depends(database.get_db)):
    sql_latlon = text("""
        SELECT 
            ST_Y(ST_Centroid(ST_SnapToGrid(location::geometry, 0.001))) as lat,
            ST_X(ST_Centroid(ST_SnapToGrid(location::geometry, 0.001))) as lon,
            AVG(rsrp) as avg_rsrp,
            COUNT(*) as count
        FROM core_networkmeasurement
        GROUP BY lat, lon
    """)
    results = db.execute(sql_latlon).fetchall()
    data = []
    for r in results:
        data.append({"lat": r.lat, "lon": r.lon, "val": r.avg_rsrp, "count": r.count})
    return data
