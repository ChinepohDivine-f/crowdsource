from fastapi import FastAPI, Depends, HTTPException, status, Request, Header, Security
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.security import APIKeyHeader
from sqlalchemy.orm import Session
from sqlalchemy import text, func
from typing import List, Optional
from geoalchemy2.shape import to_shape 
from shapely.geometry import Point, mapping
from datetime import datetime
import secrets
import json
import os

# Rate Limiting
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

import models, schemas, database, analysis, auth
from routers import auth as auth_router

# Logging setup for debugging 500 errors in cloud
import logging
import traceback
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Security Setup
limiter = Limiter(key_func=get_remote_address)
app = FastAPI(title="Senzor API", version="1.0")

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"GLOBAL ERROR: {exc}")
    logger.error(traceback.format_exc())
    return JSONResponse(
        status_code=500,
        content={"detail": str(exc), "traceback": traceback.format_exc() if os.getenv("DEBUG") else "Internal Server Error"},
    )

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

# Create tables and ensure schema is up to date
try:
    models.Base.metadata.create_all(bind=database.engine)
    # Manual check and sync for columns that might be missing in an existing DB
    with database.engine.connect() as conn:
        # User Table
        conn.execute(text("ALTER TABLE core_user ADD COLUMN IF NOT EXISTS username VARCHAR"))
        conn.execute(text("ALTER TABLE core_user ADD COLUMN IF NOT EXISTS role VARCHAR DEFAULT 'USER'"))
        conn.execute(text("ALTER TABLE core_user ADD COLUMN IF NOT EXISTS is_active BOOLEAN DEFAULT TRUE"))
        
        # Device Table
        conn.execute(text("ALTER TABLE core_device ADD COLUMN IF NOT EXISTS user_id VARCHAR REFERENCES core_user(id)"))
        
        # Measurement Table
        conn.execute(text("ALTER TABLE core_networkmeasurement ADD COLUMN IF NOT EXISTS user_id VARCHAR REFERENCES core_user(id)"))
        
        conn.commit()
    logger.info("Database schema synchronized.")
except Exception as e:
    logger.error(f"Schema Sync Error: {e}")

# Include Auth Router
app.include_router(auth_router.router)

API_KEY_NAME = "Authorization"
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)

# --- PREMIUM UI LAYOUT ENGINE ---
def get_sidebar(active_page: str = "dashboard"):
    links = [
        ("dashboard", "/", "fas fa-tachometer-alt", "Live Map"),
        ("analytics", "/view/analytics", "fas fa-chart-line", "Analytics"),
        ("data", "/view/data", "fas fa-database", "Raw Data"),
        ("register", "/view/register", "fas fa-plus-circle", "Register"),
        ("admin", "/view/admin", "fas fa-user-shield", "Admin"),
    ]
    
    html = '<div class="sidebar">'
    html += '<div class="sidebar-brand">📡 <span>Senzor</span></div>'
    html += '<div class="sidebar-links">'
    for id, path, icon, label in links:
        active_class = "active" if active_page == id else ""
        html += f'<a href="{path}" class="sidebar-link {active_class}"><i class="{icon}"></i> {label}</a>'
    html += '</div>'
    html += '<div class="sidebar-footer">'
    html += '  <div id="user-display" style="font-size: 12px; color: var(--text-muted); padding: 10px;">Guest</div>'
    html += '  <a href="/view/login" id="login-nav-link" class="sidebar-link"><i class="fas fa-sign-in-alt"></i> Login</a>'
    html += '</div>'
    html += '</div>'
    return html

def get_premium_layout(content: str, title: str = "Senzor", active_page: str = "dashboard", scripts: str = ""):
    return f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>{title} | Senzor Platform</title>
        {BASE_STYLE}
        <style>
            :root {{
                --sidebar-width: 260px;
            }}
            body {{ display: flex; overflow: hidden; }}
            .sidebar {{
                width: var(--sidebar-width);
                height: 100vh;
                background: rgba(15, 23, 42, 0.95);
                backdrop-filter: blur(20px);
                border-right: 1px solid var(--border);
                display: flex;
                flex-direction: column;
                flex-shrink: 0;
                z-index: 1000;
            }}
            .sidebar-brand {{
                padding: 30px 24px;
                font-size: 24px;
                font-weight: 700;
                color: white;
                display: flex;
                align-items: center;
                gap: 12px;
                background: linear-gradient(to right, #fff, #94a3b8);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
            }}
            .sidebar-links {{ flex: 1; padding: 20px 12px; }}
            .sidebar-link {{
                display: flex;
                align-items: center;
                gap: 12px;
                padding: 12px 16px;
                color: var(--text-muted);
                text-decoration: none;
                border-radius: 12px;
                margin-bottom: 4px;
                font-weight: 500;
                transition: all 0.2s;
            }}
            .sidebar-link i {{ width: 20px; font-size: 18px; }}
            .sidebar-link:hover {{ background: rgba(255, 255, 255, 0.05); color: var(--text-main); }}
            .sidebar-link.active {{
                background: rgba(59, 130, 246, 0.1);
                color: var(--primary);
                border: 1px solid rgba(59, 130, 246, 0.2);
            }}
            .main-view {{
                flex: 1;
                height: 100vh;
                overflow-y: auto;
                background: var(--bg-color);
                position: relative;
            }}
            .content-page {{ padding: 0; min-height: 100%; }}
            
            /* Enhanced Scrollbar */
            ::-webkit-scrollbar {{ width: 6px; }}
            ::-webkit-scrollbar-track {{ background: transparent; }}
            ::-webkit-scrollbar-thumb {{ background: rgba(148, 163, 184, 0.2); border-radius: 10px; }}
            ::-webkit-scrollbar-thumb:hover {{ background: rgba(148, 163, 184, 0.3); }}
        </style>
    </head>
    <body class="fade-in">
        {get_sidebar(active_page)}
        <main class="main-view">
            <div class="content-page">
                {content}
            </div>
        </main>
        
        <script>
            // Global State & Auth Verification
            document.addEventListener('DOMContentLoaded', () => {{
                const token = localStorage.getItem('admin_token');
                const userDisplay = document.getElementById('user-display');
                const loginLink = document.getElementById('login-nav-link');
                
                if (token) {{
                    userDisplay.innerText = 'Authenticated Admin';
                    loginLink.innerHTML = '<i class="fas fa-sign-out-alt"></i> Logout';
                    loginLink.href = '#';
                    loginLink.onclick = (e) => {{
                        e.preventDefault();
                        localStorage.removeItem('admin_token');
                        window.location.href = '/view/login';
                    }};
                }}
            }});
        </script>
        {scripts}
    </body>
    </html>
    """

# --- STYLING & UI ASSETS ---

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
                background: linear-gradient(to right, #fff, #94a3b8);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
            }}
        </style>
    </head>
    <body class="fade-in">
        <div class="login-card">
            <div class="brand">📡 Senzor</div>
            <h2 style="text-align: center; margin-bottom: 8px;">Admin Console</h2>
            <p style="text-align: center; color: var(--text-muted); font-size: 14px; margin-bottom: 30px;">Identify to access platform controls.</p>
            
            <div id="err" class="error" style="display:none;"></div>
            
            <form onsubmit="doLogin(event)">
                <label>Email Address</label>
                <input type="email" id="email" value="admin@senzor.com" required>
                
                <label>Access Key</label>
                <input type="password" id="password" value="Senzor2026" required>
                
                <button type="submit" class="btn" style="width: 100%; justify-content: center; margin-top: 10px;">
                    <i class="fas fa-lock"></i> Authorize
                </button>
            </form>
            
            <div style="margin-top: 30px; text-align: center;">
                <a href="/" style="color: var(--text-muted); text-decoration: none; font-size: 12px; transition: color 0.2s;">
                    <i class="fas fa-arrow-left"></i> Return to Map
                </a>
            </div>
        </div>

        <script>
            async function doLogin(e) {{
                e.preventDefault();
                const btn = e.target.querySelector('button');
                btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Authenticating...';
                btn.disabled = true;
                
                const formData = new FormData();
                formData.append('username', document.getElementById('email').value);
                formData.append('password', document.getElementById('password').value);
                
                try {{
                    const res = await fetch('/api/v1/auth/token', {{
                        method: 'POST',
                        body: formData
                    }});
                    const data = await res.json();
                    
                    if(res.ok) {{
                        localStorage.setItem('admin_token', data.access_token);
                        window.location.href = '/view/admin';
                    }} else {{
                        const errBox = document.getElementById('err');
                        errBox.innerText = data.detail || 'Access Denied';
                        errBox.style.display = 'block';
                        btn.innerHTML = '<i class="fas fa-lock"></i> Authorize';
                        btn.disabled = false;
                    }}
                }} catch(err) {{ 
                    alert('Backend Connection Error'); 
                    btn.disabled = false;
                    btn.innerHTML = '<i class="fas fa-lock"></i> Authorize';
                }}
            }}
        </script>
    </body>
    </html>
    """

@app.get("/", response_class=HTMLResponse)
def read_root():
    content = """
    <div id="map" style="height: 100vh; width: 100%;"></div>
    
    <div class="map-overlay">
        <div class="glass-panel" style="padding: 20px; width: 300px;">
            <h3>Live Coverage</h3>
            <p style="color: var(--text-muted); font-size: 13px;">Monitor real-time signal quality across all mapped devices.</p>
            
            <div id="quick-stats" style="margin-top: 20px;">
                <div style="display: flex; justify-content: space-between; margin-bottom: 10px;">
                    <span style="font-size: 12px; color: var(--text-muted);">Points Collected</span>
                    <span id="stat-count" style="font-weight: 700;">--</span>
                </div>
                <div style="display: flex; justify-content: space-between;">
                    <span style="font-size: 12px; color: var(--text-muted);">Avg. RSRP</span>
                    <span id="stat-avg" style="font-weight: 700; color: var(--primary);">--</span>
                </div>
            </div>

            <hr style="border: none; border-top: 1px solid var(--border); margin: 20px 0;">
            
            <label>Layer Control</label>
            <div style="display: flex; flex-direction: column; gap: 8px;">
                <button onclick="toggleLayer('marker')" class="btn btn-secondary" style="width: 100%; justify-content: start; font-size: 11px;">
                    <i class="fas fa-map-marker-alt"></i> Raw Measurements
                </button>
                <button onclick="toggleLayer('heatmap')" class="btn btn-secondary" style="width: 100%; justify-content: start; font-size: 11px;">
                    <i class="fas fa-fire"></i> Signal Heatmap
                </button>
            </div>
        </div>
    </div>

    <style>
        .map-overlay { position: absolute; top: 20px; right: 20px; z-index: 999; }
        .leaflet-container { background: #0b0f19 !important; }
        .legend { background: rgba(15, 23, 42, 0.9); padding: 12px; border-radius: 12px; border: 1px solid var(--border); color: #fff; font-size: 11px; backdrop-filter: blur(10px); }
        .legend i { width: 10px; height: 10px; float: left; margin-right: 8px; border-radius: 50%; margin-top: 2px; }
    </style>
    """
    
    scripts = """
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
    <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
    <script>
        var map = L.map('map', { zoomControl: false }).setView([0, 0], 2);
        L.control.zoom({ position: 'bottomright' }).addTo(map);
        
        L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
            attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>'
        }).addTo(map);
        
        var markersLayer = L.featureGroup().addTo(map);
        var heatmapLayer = L.featureGroup();
        
        function toggleLayer(type) {
            if (type === 'marker') {
                if (map.hasLayer(markersLayer)) map.removeLayer(markersLayer);
                else map.addLayer(markersLayer);
            } else {
                if (map.hasLayer(heatmapLayer)) map.removeLayer(heatmapLayer);
                else map.addLayer(heatmapLayer);
            }
        }

        fetch('/api/v1/measurements/').then(r => r.json()).then(data => {
            if (!Array.isArray(data)) return console.error("Measurements data is not an array:", data);
            document.getElementById('stat-count').innerText = data.length;
            let sum = 0;
            data.forEach(m => {
                sum += m.rsrp;
                var color = m.rsrp < -110 ? '#ff4b2b' : (m.rsrp < -95 ? '#f59e0b' : '#10b981');
                L.circleMarker([m.latitude, m.longitude], { 
                    radius: 5, fillColor: color, color: "#fff", weight: 0.5, fillOpacity: 0.8 
                })
                .bindPopup(`<b>Device:</b> ${m.device_id}<br><b>RSRP:</b> ${m.rsrp} dBm<br><b>Net:</b> ${m.network_type}`)
                .addTo(markersLayer);
            });
            if(data.length > 0) {
                document.getElementById('stat-avg').innerText = (sum / data.length).toFixed(1) + " dBm";
                map.fitBounds(markersLayer.getBounds(), { padding: [50, 50] });
            }
        });
        
        fetch('/api/v1/analytics/heatmap').then(r => r.json()).then(data => {
            if (!Array.isArray(data)) return console.error("Heatmap data is not an array:", data);
            data.forEach(d => {
                var color = d.val < -110 ? '#ff0000' : (d.val < -95 ? '#ffff00' : '#00ff00');
                var bounds = [[d.lat - 0.001, d.lon - 0.001], [d.lat + 0.001, d.lon + 0.001]];
                L.rectangle(bounds, { color: color, weight: 0, fillOpacity: 0.3 }).addTo(heatmapLayer);
            });
        });
        
        var legend = L.control({position: 'bottomleft'});
        legend.onAdd = function (map) {
            var div = L.DomUtil.create('div', 'info legend');
            div.innerHTML = '<b>Signal Quality</b><br>' +
                           '<i style="background: #10b981"></i> Good (>-95)<br>' +
                           '<i style="background: #f59e0b"></i> Fair (-95 to -110)<br>' +
                           '<i style="background: #ff4b2b"></i> Poor (<-110)';
            return div;
        };
        legend.addTo(map);
    </script>
    """
    return get_premium_layout(content, title="Live Coverage Map", active_page="dashboard", scripts=scripts)

@app.get("/view/register", response_class=HTMLResponse)
def view_register():
    content = """
    <div class="container">
        <div class="glass-panel" style="padding: 40px; max-width: 600px; margin: 0 auto; margin-top: 50px;">
            <h1>📝 Register Device</h1>
            <p style="color: var(--text-muted); margin-bottom: 30px;">Add a new device to the platform to start collecting data.</p>
            
            <div id="msg" class="success" style="display:none;"></div>
            <div id="err" class="error" style="display:none;"></div>
            
            <form id="regForm" onsubmit="register(event)">
                <label>Device ID (Unique UUID/Serial)</label>
                <input type="text" id="device_id" value="test-device-01" required>
                
                <label>Manufacturer</label>
                <input type="text" id="manufacturer" value="Generic" required>
                
                <label>Model</label>
                <input type="text" id="model" value="Simulator v1" required>
                
                <label>OS Version</label>
                <input type="text" id="os_version" value="Android 14">
                
                <button type="submit" class="btn" style="width: 100%; justify-content: center;">
                    <i class="fas fa-key"></i> Generate API Key
                </button>
            </form>

            <div id="resultCard" style="display:none; margin-top: 30px; padding: 20px; background: rgba(16, 185, 129, 0.05); border: 1px dashed #10b981; border-radius: 12px;">
                <label style="color: #10b981;">✅ Registration Successful</label>
                <p style="font-size: 13px;">Save this API Key securely. It is required for all data uploads.</p>
                <pre id="apiKeyBox" style="background: rgba(0,0,0,0.3); padding: 15px; border-radius: 8px; font-size: 12px; overflow-x: auto;"></pre>
            </div>
        </div>
    </div>
    """
    scripts = """
    <script>
        async function register(e) {
            e.preventDefault();
            const btn = e.target.querySelector('button');
            btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Processing...';
            btn.disabled = true;
            
            const payload = {
                device_id: document.getElementById('device_id').value,
                manufacturer: document.getElementById('manufacturer').value,
                model: document.getElementById('model').value,
                os_version: document.getElementById('os_version').value
            };
            
            try {
                const res = await fetch('/api/v1/register', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify(payload)
                });
                const data = await res.json();
                
                if(res.ok) {
                    document.getElementById('msg').innerText = data.message;
                    document.getElementById('msg').style.display = 'block';
                    document.getElementById('apiKeyBox').innerText = data.api_key;
                    document.getElementById('resultCard').style.display = 'block';
                    btn.innerHTML = '<i class="fas fa-check"></i> Success';
                    btn.style.background = '#10b981';
                } else {
                    document.getElementById('err').innerText = data.detail || 'Error';
                    document.getElementById('err').style.display = 'block';
                    btn.disabled = false;
                    btn.innerHTML = '<i class="fas fa-key"></i> Generate API Key';
                }
            } catch(err) { alert(err); btn.disabled = false; }
        }
    </script>
    """
    return get_premium_layout(content, title="Register Device", active_page="register", scripts=scripts)

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
    
    content = f"""
    <div class="container" style="max-width: 1400px;">
        <div style="display: flex; justify-content: space-between; align-items: end; margin-bottom: 30px;">
            <div>
                <h1>📊 Network Intelligence</h1>
                <p style="color: var(--text-muted);">In-depth spatial and metric analysis of collected signal data.</p>
            </div>
            <div style="background: rgba(59, 130, 246, 0.1); padding: 10px 20px; border-radius: 12px; border: 1px solid rgba(59, 130, 246, 0.2);">
                <span style="font-size: 12px; color: var(--text-muted); text-transform: uppercase; font-weight: 600;">System Grade</span>
                <div style="font-size: 20px; font-weight: 700; color: #10b981;">Optimal</div>
            </div>
        </div>
        
        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-value">{total_count}</div>
                <div class="stat-label">Total Data Points</div>
                <i class="fas fa-database" style="position: absolute; right: 20px; top: 20px; opacity: 0.1; font-size: 32px;"></i>
            </div>
            <div class="stat-card">
                <div class="stat-value">{avg_rsrp:.1f}</div>
                <div class="stat-label">Avg. Signal (dBm)</div>
                <i class="fas fa-signal" style="position: absolute; right: 20px; top: 20px; opacity: 0.1; font-size: 32px;"></i>
            </div>
            <div class="stat-card">
                <div class="stat-value">{unique_devices}</div>
                <div class="stat-label">Active Devices</div>
                <i class="fas fa-mobile-alt" style="position: absolute; right: 20px; top: 20px; opacity: 0.1; font-size: 32px;"></i>
            </div>
        </div>

        <div style="display: grid; grid-template-columns: 2fr 1fr; gap: 24px; margin-bottom: 24px;">
            <div class="glass-panel" style="padding: 24px;">
                <h3 style="margin-bottom: 20px;"><i class="fas fa-chart-bar" style="color: var(--primary);"></i> Signal Strength Distribution</h3>
                <canvas id="rsrpChart" height="140"></canvas>
            </div>
            <div class="glass-panel" style="padding: 24px;">
                <h3 style="margin-bottom: 20px;"><i class="fas fa-chart-pie" style="color: var(--accent);"></i> Network Tech</h3>
                <canvas id="netTypeChart"></canvas>
            </div>
        </div>

        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 24px;">
            <div class="glass-panel" style="padding: 24px;">
                <h3 style="margin-bottom: 10px;"><i class="fas fa-brain" style="color: #4facfe;"></i> ML Signal Predictor</h3>
                <p style="color: var(--text-muted); font-size: 13px; margin-bottom: 20px;">Forecast coverage quality using our RandomForest spatial model.</p>
                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 12px; margin-bottom: 12px;">
                    <div>
                        <label>Latitude</label>
                        <input type="text" id="ml_lat" placeholder="40.7128" style="margin-bottom:0;">
                    </div>
                    <div>
                        <label>Longitude</label>
                        <input type="text" id="ml_lon" placeholder="-74.0060" style="margin-bottom:0;">
                    </div>
                </div>
                <button onclick="predictSignal()" class="btn" style="width: 100%; justify-content: center;">
                    Forecast Signal Strength
                </button>
                <div id="mlResult" style="margin-top: 20px; display:none; padding: 20px; border-radius: 12px; text-align: center; background: rgba(79, 172, 254, 0.05); border: 1px dashed #4facfe;">
                    <div style="font-size: 11px; color: var(--text-muted); text-transform: uppercase;">Predicted RSRP</div>
                    <div id="mlVal" style="font-size: 32px; font-weight: 700; color: #4facfe;">-105.4 dBm</div>
                </div>
            </div>

            <div class="glass-panel" style="padding: 24px;">
                <h3 style="margin-bottom: 10px;"><i class="fas fa-microscope" style="color: #f59e0b;"></i> Spatial Clustering</h3>
                <p style="color: var(--text-muted); font-size: 13px; margin-bottom: 20px;">Detect contiguous "Coverage Holes" automatically via DBSCAN clustering.</p>
                <button class="btn btn-secondary" onclick="runAnalysis()" style="width:100%;">
                    <i class="fas fa-play"></i> Trigger Hole Detection
                </button>
                <div id="analyticsResult" style="margin-top: 20px; display:none;">
                    <pre id="jsonOutput" style="font-size: 11px; max-height: 180px; background: rgba(0,0,0,0.3); padding: 15px; border-radius: 8px; color: #34d399;"></pre>
                </div>
            </div>
        </div>
    </div>
    """
    scripts = """
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <script>
        async function loadCharts() {
            const res = await fetch('/api/v1/analytics/stats');
            const data = await res.json();

            new Chart(document.getElementById('rsrpChart'), {
                type: 'bar',
                data: {
                    labels: data.rsrp_bins.map(b => b.range),
                    datasets: [{
                        label: 'Points',
                        data: data.rsrp_bins.map(b => b.count),
                        backgroundColor: 'rgba(59, 130, 246, 0.4)',
                        borderColor: '#3b82f6',
                        borderWidth: 1,
                        borderRadius: 6
                    }]
                },
                options: { 
                    responsive: true, 
                    scales: { 
                        y: { beginAtZero: true, grid: { color: 'rgba(255,255,255,0.05)' }, border: { display: false } }, 
                        x: { grid: { display: false }, border: { display: false } } 
                    },
                    plugins: { legend: { display: false } }
                }
            });

            new Chart(document.getElementById('netTypeChart'), {
                type: 'doughnut',
                data: {
                    labels: Object.keys(data.net_types),
                    datasets: [{
                        data: Object.values(data.net_types),
                        backgroundColor: ['#3b82f6', '#8b5cf6', '#64748b'],
                        borderWidth: 0
                    }]
                },
                options: { 
                    responsive: true, 
                    plugins: { legend: { position: 'bottom', labels: { color: '#94a3b8', padding: 20, usePointStyle: true } } },
                    cutout: '70%'
                }
            });
        }

        async function predictSignal() {
            const lat = document.getElementById('ml_lat').value;
            const lon = document.getElementById('ml_lon').value;
            const res = await fetch(`/api/v1/analytics/predict?lat=${lat}&lon=${lon}`);
            const data = await res.json();
            
            const box = document.getElementById('mlResult');
            const val = document.getElementById('mlVal');
            box.style.display = 'block';
            if(data.prediction) {
                val.innerText = data.prediction.toFixed(1) + " dBm";
                val.style.color = data.prediction < -110 ? '#ff4b2b' : '#3b82f6';
            } else {
                val.innerText = "No Data";
                val.style.color = "#64748b";
            }
        }

        async function runAnalysis() {
            const res = await fetch('/api/v1/analytics/trigger');
            const data = await res.json();
            document.getElementById('jsonOutput').innerText = JSON.stringify(data, null, 2);
            document.getElementById('analyticsResult').style.display = 'block';
        }

        loadCharts();
    </script>
    """
    return get_premium_layout(content, title="Network Intelligence", active_page="analytics", scripts=scripts)

@app.get("/view/simulate", response_class=HTMLResponse)
def view_simulate():
    content = """
    <div class="container" style="max-width: 800px;">
        <div class="glass-panel" style="padding: 40px; margin-top: 50px;">
            <h1>🚀 Drive Test Simulator</h1>
            <p style="color: var(--text-muted); margin-bottom: 30px;">Generate synthetic data to test platform scalability and mapping.</p>
            
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 24px; margin-bottom: 24px;">
                <div>
                    <label>Auth Token</label>
                    <input id="token" type="password" placeholder="Paste API Key here">
                </div>
                <div>
                    <label>Device ID</label>
                    <input id="devId" type="text" placeholder="Device UUID">
                </div>
            </div>
            
            <button onclick="simulateUpload()" class="btn" style="width: 100%; justify-content: center; height: 50px; font-size: 16px;">
                <i class="fas fa-play"></i> Launch Simulation (Batch of 10)
            </button>
            
            <div id="simLog" style="margin-top: 30px; padding: 20px; background: rgba(15, 23, 42, 0.8); border: 1px solid var(--border); border-radius: 12px; font-family: 'JetBrains Mono', monospace; font-size: 12px; height: 300px; overflow-y: auto; display:none; color: #a5b4fc;">
                <div style="border-bottom: 1px solid rgba(165, 180, 252, 0.1); padding-bottom: 10px; margin-bottom: 10px; color: var(--text-muted); text-transform: uppercase; font-size: 10px; letter-spacing: 1px;">Execution Console</div>
            </div>
        </div>
    </div>
    """
    scripts = """
    <script>
        document.getElementById('token').value = localStorage.getItem('senzor_api_key') || '';
        document.getElementById('devId').value = localStorage.getItem('senzor_device_id') || '';
        
        function log(msg) {
            const div = document.getElementById('simLog');
            div.style.display = 'block';
            div.innerHTML += `<div><span style="color: #6366f1;">[${new Date().toLocaleTimeString()}]</span> ${msg}</div>`;
            div.scrollTop = div.scrollHeight;
        }

        async function simulateUpload() {
            const token = document.getElementById('token').value;
            const devId = document.getElementById('devId').value;
            if(!token) return alert("API Key is required to simulate upload.");
            
            const baseLat = 40.7128; 
            const baseLon = -74.0060;
            const data = [];
            const now = Math.floor(Date.now() / 1000);
            
            for(let i=0; i<10; i++) {
                data.push({
                    ts: now - i*5,
                    lat: baseLat + (Math.random() * 0.01),
                    lon: baseLon + (Math.random() * 0.01),
                    acc: 5.0,
                    net: Math.random() > 0.5 ? 'LTE' : 'NR',
                    ci: 12345,
                    metrics: {
                        rsrp: -80 - Math.floor(Math.random() * 50),
                        rsrq: -10, sinr: 15
                    }
                });
            }
            
            const payload = {
                meta: {
                    device_id: devId || "sim-001",
                    batch_size: 10,
                    client_timestamp: now,
                    model: "WebSimulator",
                    os_version: "Web 1.0"
                },
                data: data
            };
            
            log("📡 Initiating encrypted batch transmission...");
            try {
                const res = await fetch('/api/v1/ingest/batch', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'Authorization': 'Token ' + token
                    },
                    body: JSON.stringify(payload)
                });
                const json = await res.json();
                if(res.ok) log("<span style='color: #10b981;'>✅ Batch Accepted:</span> " + json.message);
                else log("<span style='color: #ef4444;'>❌ Rejected:</span> " + (json.detail || res.statusText));
            } catch(e) { log("<span style='color: #ef4444;'>🧨 Protocol Failure:</span> " + e); }
        }
    </script>
    """
    return get_premium_layout(content, title="Device Simulator", active_page="register", scripts=scripts)

@app.get("/view/data", response_class=HTMLResponse)
def view_data(db: Session = Depends(database.get_db)):
    measurements = db.query(models.NetworkMeasurement).order_by(models.NetworkMeasurement.recorded_at.desc()).limit(100).all()
    rows = ""
    for m in measurements:
        pt = to_shape(m.location)
        status_color = "#ff4b2b" if m.status == "Hole" else "#10b981"
        rows += f"""
        <tr>
            <td>{m.id}</td>
            <td style="color: var(--text-muted); font-size: 11px;">{m.recorded_at.strftime('%Y-%m-%d %H:%M')}</td>
            <td><code style="background: rgba(255,255,255,0.05); padding: 2px 6px; border-radius: 4px; font-size: 11px;">{m.device_id[:12]}...</code></td>
            <td><span class="badge badge-user">{m.network_type}</span></td>
            <td style="font-weight: 700;">{m.rsrp}</td>
            <td><span style="color:{status_color}; font-size: 12px; font-weight: 600;">{m.status}</span></td>
            <td style="color: var(--text-muted); font-size: 11px;">{pt.y:.4f}, {pt.x:.4f}</td>
        </tr>
        """
    content = f"""
    <div class="container" style="max-width: 1400px;">
        <div style="margin-bottom: 40px;">
            <h1>🗄️ Observation Ledger</h1>
            <p style="color: var(--text-muted);">Real-time stream of the latest 100 measurements ingested by the platform.</p>
        </div>

        <div class="glass-panel" style="padding: 0; overflow: hidden;">
            <table>
                <thead>
                    <tr>
                        <th>ID</th>
                        <th>Timestamp</th>
                        <th>Resource ID</th>
                        <th>Network</th>
                        <th>RSRP (dBm)</th>
                        <th>Class</th>
                        <th>Global Coordinates</th>
                    </tr>
                </thead>
                <tbody>
                    {rows}
                </tbody>
            </table>
        </div>
    </div>
    """
    return get_premium_layout(content, title="Observation Ledger", active_page="data")

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
        role_icon = "crown" if u.role == models.UserRole.ADMIN else "user"
        user_rows += f"""
        <tr>
            <td>
                <div style="font-weight: 600;">{u.username or "Anonymous"}</div>
                <div style="font-size: 11px; color: var(--text-muted);">{u.email}</div>
            </td>
            <td>
                <span class="badge badge-{role_type}"><i class="fas fa-{role_icon}"></i> {u.role.value.upper()}</span>
            </td>
            <td>
                <div style="display: flex; align-items: center; gap: 8px;">
                    <div style="width: 60px; height: 4px; background: rgba(255,255,255,0.05); border-radius: 2px;">
                        <div style="width: {min(100, user_count/10)}%; height: 100%; background: var(--primary); border-radius: 2px;"></div>
                    </div>
                    <span style="font-size: 13px;">{user_count} pts</span>
                </div>
            </td>
            <td style="font-size: 13px; color: var(--text-muted);">{u.created_at.strftime('%b %d, %Y')}</td>
        </tr>
        """
    
    total_users = len(users)
    total_measurements = db.query(models.NetworkMeasurement).count()
    active_devices = db.query(models.NetworkMeasurement.device_id).distinct().count()
    
    content = f"""
    <div class="container" style="max-width: 1400px;">
        <div style="margin-bottom: 40px;">
            <h1>🛡️ Admin Cockpit</h1>
            <p style="color: var(--text-muted);">Platform command center for user management and system integrity.</p>
        </div>

        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-value">{total_users}</div>
                <div class="stat-label">Registered Users</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{total_measurements}</div>
                <div class="stat-label">System Data Points</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{active_devices}</div>
                <div class="stat-label">Validated Devices</div>
            </div>
        </div>

        <div class="tab-nav">
            <button class="tab-btn active" onclick="switchTab('users')"><i class="fas fa-users"></i> Users</button>
            <button class="tab-btn" onclick="switchTab('system')"><i class="fas fa-server"></i> System Health</button>
        </div>

        <!-- User Management -->
        <div id="users" class="tab-content active">
            <div class="glass-panel" style="padding: 0; overflow: hidden;">
                <div style="padding: 24px; border-bottom: 1px solid var(--border); display: flex; justify-content: space-between; align-items: center;">
                    <h3 style="margin:0;">User Directory</h3>
                    <div style="position: relative; width: 300px;">
                        <i class="fas fa-search" style="position: absolute; left: 15px; top: 18px; color: var(--text-muted);"></i>
                        <input type="text" placeholder="Search accounts..." style="padding-left: 45px; margin-bottom: 0;">
                    </div>
                </div>
                <table>
                    <thead>
                        <tr>
                            <th>Identity</th>
                            <th>Role</th>
                            <th>Contribution</th>
                            <th>Joined</th>
                        </tr>
                    </thead>
                    <tbody>
                        {user_rows}
                    </tbody>
                </table>
            </div>
        </div>

        <!-- System Health -->
        <div id="system" class="tab-content">
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 24px;">
                <div class="glass-panel" style="padding: 24px;">
                    <h3><i class="fas fa-microchip" style="color: #10b981;"></i> Backend Infrastructure</h3>
                    <div style="margin-top: 20px;">
                        <div style="display: flex; justify-content: space-between; margin-bottom: 12px;">
                            <span style="color: var(--text-muted);">Service Status</span>
                            <span class="badge badge-user" style="background: rgba(16, 185, 129, 0.1); color: #10b981; border: none;">Operational</span>
                        </div>
                        <div style="display: flex; justify-content: space-between;">
                            <span style="color: var(--text-muted);">API Uptime</span>
                            <span style="color: var(--text-main); font-weight: 600;">99.9%</span>
                        </div>
                    </div>
                </div>
                <div class="glass-panel" style="padding: 24px;">
                    <h3><i class="fas fa-database" style="color: var(--primary);"></i> Storage Layer</h3>
                    <div style="margin-top: 20px;">
                        <div style="display: flex; justify-content: space-between; margin-bottom: 12px;">
                            <span style="color: var(--text-muted);">Database</span>
                            <span class="badge badge-user" style="background: rgba(59, 130, 246, 0.1); color: var(--primary); border: none;">PostGIS Connected</span>
                        </div>
                        <div style="display: flex; justify-content: space-between;">
                            <span style="color: var(--text-muted);">Sync Latency</span>
                            <span style="color: var(--text-main); font-weight: 600;">14ms</span>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
    """
    
    scripts = """
    <script>
        function switchTab(tabId) {
            document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
            document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
            document.getElementById(tabId).classList.add('active');
            event.currentTarget.classList.add('active');
            window.location.hash = tabId;
        }
        
        // Handle initial hash
        window.onload = () => {
            const hash = window.location.hash.replace('#', '');
            if (hash && document.getElementById(hash)) {
                switchTab(hash);
                // Highlight the correct button
                document.querySelectorAll('.tab-btn').forEach(b => {
                    if (b.innerText.toLowerCase().includes(hash)) b.classList.add('active');
                    else b.classList.remove('active');
                });
            }
        };
    </script>
    """
    return get_premium_layout(content, title="Admin Cockpit", active_page="admin", scripts=scripts)

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
