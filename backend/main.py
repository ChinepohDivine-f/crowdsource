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
# --- NAVIGATION & UI COMPONENTS ---
NAV_HTML = """
<nav style="background: rgba(15, 23, 42, 0.8); backdrop-filter: blur(10px); border-bottom: 1px solid rgba(148, 163, 184, 0.1); padding: 15px 0; position: sticky; top: 0; z-index: 100;">
    <div style="max-width: 1200px; margin: 0 auto; padding: 0 20px; display: flex; justify-content: space-between; align-items: center;">
        <div style="display: flex; align-items: center; gap: 10px;">
            <div style="width: 32px; height: 32px; background: linear-gradient(135deg, #3b82f6, #8b5cf6); border-radius: 8px; display: flex; align-items: center; justify-content: center;">
                <span style="color: white; font-size: 18px;">📡</span>
            </div>
            <div style="font-weight: 700; font-size: 20px; background: linear-gradient(to right, #fff, #94a3b8); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">
                Senzor <span style="font-weight: 400; font-size: 14px; color: #64748b; -webkit-text-fill-color: #64748b; margin-left: 5px;">Admin</span>
            </div>
        </div>
        <div>
            <a href="/" class="nav-link">Dashboard</a>
            <a href="/view/register" class="nav-link">Register Device</a>
            <a href="/view/analytics" class="nav-link">Analytics</a>
            <a href="/view/data" class="nav-link">Data</a>
            <a href="/view/admin" class="nav-link" style="color: #3b82f6;">Admin Panel</a>
            <a href="/docs" target="_blank" class="nav-link" style="color: #8b5cf6;">API ↗</a>
        </div>
    </div>
</nav>
"""

BASE_STYLE = """
<link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700&display=swap" rel="stylesheet">
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
<style>
    :root {
        --bg-color: #0f172a;
        --card-bg: rgba(30, 41, 59, 0.6);
        --primary: #3b82f6;
        --accent: #8b5cf6;
        --text-main: #f8fafc;
        --text-muted: #94a3b8;
        --border: rgba(148, 163, 184, 0.1);
        --glass: blur(16px);
        --gradient: linear-gradient(135deg, var(--primary), var(--accent));
    }
    
    * { box-sizing: border-box; }
    body { font-family: 'Outfit', sans-serif; margin: 0; padding: 0; background: var(--bg-color); color: var(--text-main); min-height: 100vh; overflow-x: hidden; }
    
    .glass-panel { background: var(--card-bg); backdrop-filter: var(--glass); -webkit-backdrop-filter: var(--glass); border: 1px solid var(--border); border-radius: 16px; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06); }
    
    .container { max-width: 1200px; margin: 40px auto; padding: 0 20px; }
    
    h1, h2, h3 { font-weight: 600; color: var(--text-main); margin-top: 0; }
    h1 { font-size: 2.5rem; letter-spacing: -0.02em; background: linear-gradient(to right, #fff, #94a3b8); -webkit-background-clip: text; -webkit-text-fill-color: transparent; margin-bottom: 1.5rem; }
    
    .card { background: var(--card-bg); backdrop-filter: var(--glass); border: 1px solid var(--border); border-radius: 16px; padding: 24px; margin-bottom: 24px; transition: transform 0.2s, box-shadow 0.2s; }
    .card:hover { transform: translateY(-2px); box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1); border-color: rgba(59, 130, 246, 0.3); }
    
    .btn { padding: 12px 24px; background: var(--gradient); color: white; border: none; border-radius: 8px; font-weight: 600; cursor: pointer; transition: all 0.2s; text-transform: uppercase; font-size: 0.85rem; letter-spacing: 0.5px; display: inline-flex; align-items: center; gap: 8px; }
    .btn:hover { transform: translateY(-2px); box-shadow: 0 10px 15px -3px rgba(59, 130, 246, 0.4); filter: brightness(1.1); }
    .btn-secondary { background: rgba(255, 255, 255, 0.05); border: 1px solid var(--border); color: var(--text-muted); }
    .btn-secondary:hover { background: rgba(255, 255, 255, 0.1); color: var(--text-main); }
    
    input, select { width: 100%; padding: 14px; background: rgba(15, 23, 42, 0.6); border: 1px solid var(--border); color: var(--text-main); border-radius: 8px; margin-bottom: 20px; transition: border-color 0.2s; font-family: inherit; }
    input:focus, select:focus { outline: none; border-color: var(--primary); box-shadow: 0 0 0 2px rgba(59, 130, 246, 0.2); }
    label { display: block; margin-bottom: 8px; color: var(--text-muted); font-size: 0.85rem; font-weight: 500; text-transform: uppercase; letter-spacing: 0.05em; }
    
    table { width: 100%; border-collapse: separate; border-spacing: 0; }
    th { text-align: left; padding: 16px; color: var(--text-muted); border-bottom: 1px solid var(--border); font-weight: 500; text-transform: uppercase; font-size: 0.75rem; letter-spacing: 0.1em; }
    td { padding: 16px; border-bottom: 1px solid var(--border); color: var(--text-main); vertical-align: middle; }
    tr:last-child td { border-bottom: none; }
    tr { transition: background-color 0.2s; }
    tr:hover td { background-color: rgba(255, 255, 255, 0.02); }
    
    .badge { padding: 6px 12px; border-radius: 20px; font-size: 0.75rem; font-weight: 600; display: inline-flex; align-items: center; gap: 6px; }
    .badge-admin { background: rgba(139, 92, 246, 0.15); color: #c4b5fd; border: 1px solid rgba(139, 92, 246, 0.3); }
    .badge-user { background: rgba(59, 130, 246, 0.15); color: #93c5fd; border: 1px solid rgba(59, 130, 246, 0.3); }
    
    .nav-link { color: var(--text-muted); text-decoration: none; margin-left: 24px; font-size: 0.9rem; font-weight: 500; transition: color 0.2s; }
    .nav-link:hover { color: var(--text-main); }
    
    .stats-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); gap: 24px; margin-bottom: 32px; }
    .stat-card { background: linear-gradient(145deg, rgba(30,41,59,0.4), rgba(15,23,42,0.4)); padding: 24px; border-radius: 16px; border: 1px solid var(--border); position: relative; overflow: hidden; }
    .stat-card::after { content: ''; position: absolute; top: 0; left: 0; width: 100%; height: 4px; background: var(--gradient); opacity: 0.5; }
    .stat-value { font-size: 2.5rem; font-weight: 700; color: var(--text-main); margin-bottom: 4px; letter-spacing: -0.02em; }
    .stat-label { color: var(--text-muted); font-size: 0.875rem; font-weight: 500; }
    
    .fade-in { animation: fadeIn 0.5s ease-out; }
    @keyframes fadeIn { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: translateY(0); } }
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

@app.get("/view/login", response_class=HTMLResponse)
def view_login():
    """Admin login page."""
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Senzor Admin Login</title>
        {BASE_STYLE}
        <style>
            body {{
                background-image: radial-gradient(circle at 10% 20%, rgba(59, 130, 246, 0.15) 0%, transparent 20%),
                                radial-gradient(circle at 90% 80%, rgba(139, 92, 246, 0.15) 0%, transparent 20%);
                display: flex;
                align-items: center;
                justify-content: center;
            }}
            .login-container {{
                width: 100%;
                max-width: 420px;
                padding: 40px;
            }}
            .brand {{
                text-align: center;
                margin-bottom: 30px;
            }}
            .brand-icon {{
                font-size: 48px;
                margin-bottom: 10px;
                display: block;
            }}
        </style>
    </head>
    <body>
        <div class="login-container fade-in">
            <div class="glass-panel" style="padding: 40px;">
                <div class="brand">
                    <span class="brand-icon">📡</span>
                    <h1 style="font-size: 24px; margin: 0;">Admin Portal</h1>
                    <p style="color: var(--text-muted);">Sign in to manage your network</p>
                </div>
                
                <div id="error" class="error" style="display:none; text-align: center;"></div>
                
                <form onsubmit="login(event)">
                    <label>Email Address</label>
                    <input type="email" id="email" value="admin@senzor.com" required placeholder="name@company.com">
                    
                    <label>Password</label>
                    <input type="password" id="password" required placeholder="••••••••">
                    
                    <button type="submit" class="btn" style="width: 100%; justify-content: center;">
                        <span>Sign In</span> <i class="fas fa-arrow-right"></i>
                    </button>
                    
                    <div style="margin-top: 20px; text-align: center; font-size: 13px; color: var(--text-muted);">
                        Secure Drive Test Management System &copy; 2026
                    </div>
                </form>
            </div>
        </div>
        
        <script>
            async function login(e) {{
                e.preventDefault();
                const email = document.getElementById('email').value;
                const password = document.getElementById('password').value;
                const btn = document.querySelector('button');
                const errBox = document.getElementById('error');
                
                btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Authenticating...';
                btn.disabled = true;
                errBox.style.display = 'none';
                
                try {{
                    const formData = new URLSearchParams();
                    formData.append('username', email);
                    formData.append('password', password);
                    
                    const res = await fetch('/api/v1/auth/token', {{
                        method: 'POST',
                        headers: {{'Content-Type': 'application/x-www-form-urlencoded'}},
                        body: formData
                    }});
                    
                    const data = await res.json();
                    
                    if (res.ok) {{
                        localStorage.setItem('admin_token', data.access_token);
                        btn.innerHTML = '<i class="fas fa-check"></i> Success';
                        btn.style.background = '#10b981';
                        setTimeout(() => window.location.href = '/view/admin', 500);
                    }} else {{
                        throw new Error(data.detail || 'Login failed');
                    }}
                }} catch (err) {{
                    btn.innerHTML = '<span>Sign In</span> <i class="fas fa-arrow-right"></i>';
                    btn.disabled = false;
                    btn.style.background = '';
                    errBox.innerText = err.message;
                    errBox.style.display = 'block';
                }}
            }}
        </script>
    </body>
    </html>
    """

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
            <td style="padding: 10px;">{m.device_id[:8] if m.device_id else 'N/A'}...</td>
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

@app.get("/view/admin", response_class=HTMLResponse)
def view_admin(db: Session = Depends(database.get_db)):
    """Admin dashboard - requires login."""
    # Get all users
    users = db.query(models.User).order_by(models.User.created_at.desc()).all()
    user_rows = ""
    for u in users:
        user_count = db.query(models.NetworkMeasurement).filter(
            models.NetworkMeasurement.user_id == u.id
        ).count()
        role_type = "admin" if u.role == models.UserRole.ADMIN else "user"
        role_badge = f'<span class="badge badge-{role_type}"><i class="fas fa-{"crown" if u.role == models.UserRole.ADMIN else "user"}"></i> {u.role.value.upper()}</span>'
        user_rows += f"""
        <tr>
            <td>
                <div style="font-weight: 600;">{u.username or "No Username"}</div>
                <div style="font-size: 11px; color: var(--text-muted);">{u.email}</div>
            </td>
            <td>{role_badge}</td>
            <td>
                <div style="display: flex; align-items: center; gap: 8px;">
                    <div style="width: 60px; height: 4px; background: rgba(255,255,255,0.1); border-radius: 2px;">
                        <div style="width: {min(100, user_count/10)}%; height: 100%; background: var(--primary); border-radius: 2px;"></div>
                    </div>
                    {user_count}
                </div>
            </td>
            <td>{u.created_at.strftime('%Y-%m-%d')}</td>
        </tr>
        """
    
    total_users = len(users)
    total_measurements = db.query(models.NetworkMeasurement).count()
    active_devices = db.query(models.NetworkMeasurement.device_id).distinct().count()
    
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Senzor Admin Dashboard</title>
        {BASE_STYLE}
        <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
        <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
        <style>
            .dashboard-header {{
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin-bottom: 30px;
            }}
            .tab-nav {{
                display: flex;
                gap: 20px;
                border-bottom: 1px solid var(--border);
                margin-bottom: 30px;
            }}
            .tab-btn {{
                background: none;
                border: none;
                color: var(--text-muted);
                padding: 15px 5px;
                cursor: pointer;
                font-size: 0.95rem;
                font-weight: 500;
                position: relative;
                transition: color 0.3s;
            }}
            .tab-btn.active {{
                color: var(--primary);
            }}
            .tab-btn.active::after {{
                content: '';
                position: absolute;
                bottom: -1px;
                left: 0;
                width: 100%;
                height: 2px;
                background: var(--primary);
                box-shadow: 0 -2px 10px var(--primary);
            }}
            .tab-content {{ display: none; animation: fadeIn 0.4s; }}
            .tab-content.active {{ display: block; }}
            
            #adminMap {{ height: 500px; width: 100%; border-radius: 12px; z-index: 1; }}
        </style>
    </head>
    <body style="opacity: 0; transition: opacity 0.5s;">
        {NAV_HTML}
        
        <div class="container">
            <div class="dashboard-header">
                <div>
                    <h1>Overview</h1>
                    <p style="color: var(--text-muted); margin-top: -20px;">Welcome back, Admin</p>
                </div>
                <button onclick="logout()" class="btn btn-secondary">
                    <i class="fas fa-sign-out-alt"></i> Logout
                </button>
            </div>
            
            <div class="stats-grid">
                <div class="stat-card">
                    <div class="stat-value">{total_users}</div>
                    <div class="stat-label">Total Users</div>
                    <i class="fas fa-users" style="position: absolute; right: 20px; top: 20px; opacity: 0.1; font-size: 40px;"></i>
                </div>
                <div class="stat-card">
                    <div class="stat-value">{total_measurements}</div>
                    <div class="stat-label">Data Points</div>
                    <i class="fas fa-database" style="position: absolute; right: 20px; top: 20px; opacity: 0.1; font-size: 40px;"></i>
                </div>
                <div class="stat-card">
                    <div class="stat-value">{active_devices}</div>
                    <div class="stat-label">Active Devices</div>
                    <i class="fas fa-mobile-alt" style="position: absolute; right: 20px; top: 20px; opacity: 0.1; font-size: 40px;"></i>
                </div>
            </div>
            
            <div class="tab-nav">
                <button class="tab-btn active" onclick="switchTab('users')">👥 User Management</button>
                <button class="tab-btn" onclick="switchTab('map')">🗺️ Live Map</button>
                <button class="tab-btn" onclick="switchTab('system')">⚙️ System Health</button>
            </div>
            
            <!-- User Tab -->
            <div id="users" class="tab-content active">
                <div class="card">
                    <div style="display: flex; justify-content: space-between; margin-bottom: 20px;">
                        <h3>User Directory</h3>
                        <input type="text" placeholder="Search users..." style="width: 250px; margin: 0; padding: 8px 12px;">
                    </div>
                    <table>
                        <thead>
                            <tr>
                                <th>User</th>
                                <th>Role</th>
                                <th>Contribution Level</th>
                                <th>Joined</th>
                            </tr>
                        </thead>
                        <tbody>
                            {user_rows}
                        </tbody>
                    </table>
                </div>
            </div>
            
            <!-- Map Tab -->
            <div id="map" class="tab-content">
                <div class="card" style="padding: 0; overflow: hidden;">
                    <div id="adminMap"></div>
                </div>
            </div>
            
             <!-- System Tab -->
            <div id="system" class="tab-content">
                <div class="card">
                    <h3>System Status</h3>
                    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-top: 20px;">
                        <div>
                            <label>Backend API</label>
                            <div class="badge badge-user" style="background: rgba(16, 185, 129, 0.2); color: #34d399; border-color: rgba(16, 185, 129, 0.4);">
                                <i class="fas fa-check-circle"></i> Operational
                            </div>
                        </div>
                         <div>
                            <label>PostGIS Database</label>
                            <div class="badge badge-user" style="background: rgba(16, 185, 129, 0.2); color: #34d399; border-color: rgba(16, 185, 129, 0.4);">
                                <i class="fas fa-database"></i> Connected
                            </div>
                        </div>
                    </div>
                </div>
            </div>

        </div>
        
        <script>
            // Auth Check
            const token = localStorage.getItem('admin_token');
            if (!token) {{
                window.location.href = '/view/login';
            }} else {{
                document.body.style.opacity = '1';
            }}
            
            function logout() {{
                localStorage.removeItem('admin_token');
                window.location.href = '/view/login';
            }}
            
            function switchTab(tabId) {{
                document.querySelectorAll('.tab-content').forEach(el => el.classList.remove('active'));
                document.querySelectorAll('.tab-btn').forEach(el => el.classList.remove('active'));
                document.getElementById(tabId).classList.add('active');
                event.target.classList.add('active');
                
                if(tabId === 'map' && !window.mapInitialized) {{
                    initMap();
                }}
            }}
            
            window.mapInitialized = false;
            function initMap() {{
                setTimeout(() => {{
                    var map = L.map('adminMap').setView([0, 0], 2);
                    L.tileLayer('https://{{s}}.tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png', {{ attribution: '© OpenStreetMap' }}).addTo(map);
                    
                    fetch('/api/v1/measurements/').then(r => r.json()).then(data => {{
                        var markers = L.featureGroup();
                        data.forEach(m => {{
                            var color = m.rsrp < -110 ? '#ef4444' : '#22d3ee';
                            L.circleMarker([m.latitude, m.longitude], {{ radius: 5, fillColor: color, color: "white", weight: 1, fillOpacity: 0.8 }})
                            .bindPopup(`<b>User:</b> ${{m.device_id}}<br><b>RSRP:</b> ${{m.rsrp}} dBm`).addTo(markers);
                        }});
                        markers.addTo(map);
                        if(data.length > 0) map.fitBounds(markers.getBounds());
                    }});
                    window.mapInitialized = true;
                }}, 100);
            }}
        </script>
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
async def ingest_batch(
    payload: schemas.BatchPayload, 
    authorization: Optional[str] = Header(None),
    db: Session = Depends(database.get_db)
):
    """Ingest batch data. Supports both Device API Key (Token) and User JWT (Bearer)."""
    
    print(f"DEBUG: Ingest Batch Hit. Device: {payload.meta.device_id}, Size: {len(payload.data)}")
    
    device_id = None
    user_id = None
    
    if not authorization:
        print("DEBUG: Missing Auth Header")
        raise HTTPException(status_code=401, detail="Missing Authorization Header")
    
    try:
        parts = authorization.split()
        if len(parts) != 2:
            raise HTTPException(status_code=401, detail="Invalid Auth Header Format")
            
        scheme, token = parts
        
        if scheme.lower() == 'bearer':
            # User JWT - authenticate and link to user
            try:
                # Ensure we're using the correct secret key
                current_user = await auth.get_current_user(token, db)
                user_id = current_user.id
                print(f"DEBUG: Authenticated User: {current_user.email} ({user_id})")
                
                # Get or create device for this user
                device = db.query(models.DeviceProfile).filter(models.DeviceProfile.id == payload.meta.device_id).first()
                if not device:
                    print(f"DEBUG: Registering new device for user: {payload.meta.device_id}")
                    device = models.DeviceProfile(
                        id=payload.meta.device_id,
                        user_id=user_id,
                        manufacturer=payload.meta.manufacturer,
                        model=payload.meta.model,
                        os_version=payload.meta.os_version,
                        api_key=None # API Key not needed for user-owned devices
                    )
                    db.add(device)
                    db.commit()
                elif device.user_id != user_id:
                     # Optional: Claim device if unclaimed? For now, just log warning
                     print(f"DEBUG: Device {payload.meta.device_id} exists but user mismatch (Expected {user_id}, got {device.user_id})")
                     # We still allow ingestion, but maybe don't link device ownership if already taken
                
                device_id = payload.meta.device_id

            except Exception as e:
                print(f"DEBUG: Bearer Auth Failed: {str(e)}")
                raise HTTPException(status_code=401, detail=f"Invalid Bearer token: {str(e)}")
        
        elif scheme.lower() == 'token':
             # Legacy Device API Key
             print(f"DEBUG: Simulating Device Token Auth: {token[:10]}...")
             device = db.query(models.DeviceProfile).filter(models.DeviceProfile.api_key == token).first()
             if not device:
                 print("DEBUG: Invalid Device Token")
                 raise HTTPException(status_code=403, detail="Invalid API Key")
             device_id = device.id
             print(f"DEBUG: Authenticated Device: {device_id}")
             
        else:
            raise HTTPException(status_code=401, detail="Invalid Auth Scheme")
            
    except HTTPException as he:
        raise he
    except Exception as e:
        print(f"DEBUG: Auth Logic Error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Auth processing error: {str(e)}")

    # Process Data
    try:
        measurements = []
        for item in payload.data:
            recorded_at = datetime.fromtimestamp(item.ts)
            rsrp = item.metrics.get("rsrp", -140)
            status_val = "Hole" if rsrp < -110 else "Good"
            
            measurement = models.NetworkMeasurement(
                device_id=device_id,
                user_id=user_id,  # Link to authenticated user
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
    except Exception as e:
        db.rollback()
        print(f"Error processing batch: {e}")
        raise HTTPException(status_code=500, detail=f"Error processing batch: {str(e)}")
        
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
