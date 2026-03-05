# Senzor: Crowdsensed Drive Test Platform 📡

A professional-grade Mobile-to-Cloud crowdsensing system for cellular network monitoring and spatial analysis. Senzor captures real-time network metrics (RSRP, SINR, RSRQ) and leverages Machine Learning to predict coverage and identify network holes.

---

## 🌟 Key Features

### 📱 Mobile Experience (Flutter)
- **Native Telephony Integration**: Accesses low-level Android telephony APIs via a custom Kotlin bridge for accurate signal reporting.
- **Offline-First Buffering**: Uses SQLite to cache measurements when offline, with an intelligent store-and-forward batch sync system.
- **Minimalist Dashboard**: Real-time visualization of signal quality metrics with dynamic color-coding based on 3GPP standards.
- **Background Sync**: Automated data ingestion using JWT-secured batch endpoints.

### 🌐 Web Command Center (FastAPI)
- **Live Intelligence Map**: Global visualization of signal strength with interactive data point inspection.
- **Network Analytics**: dedicated dashboard for signal distribution, network mix (4G/5G), and average performance metrics.
- **Direct Observation Ledger**: A live-stream of the most recent 100 observations ingested by the platform.
- **Device Simulator**: Built-in web tool to simulate high-volume drive tests for platform stress testing.
- **Admin Cockpit**: Comprehensive management of users, devices, and system health with data export (CSV) capabilities.

### 🧠 Intelligence & Analytics
- **Coverage Hole Detection**: Uses **DBSCAN** spatial clustering to automatically identify clusters of poor signal points (RSRP < -110 dBm).
- **Predictive Modeling**: Implements a **Random Forest Regressor** to predict signal strength at any coordinate based on historical crowdsensed data.

---

## 🏗 System Architecture

1. **Client**: Flutter (Android) with Provider state management and Native Kotlin Bridge.
2. **Gateway**: FastAPI (Python 3.11) with SlowAPI rate limiting and JWT/Bearer authentication.
3. **Storage**: PostgreSQL 15 + PostGIS 3.3 for high-performance spatial queries and time-series data.
4. **DevOps**: Docker & Docker Compose orchestration for unified local development.

---

## 🚀 Quick Start (Local Setup)

### 1. Database (Docker)
Start the PostGIS spatial engine:
```bash
docker run --name crowdsource_db \
  -e POSTGRES_USER=user \
  -e POSTGRES_PASSWORD=password \
  -e POSTGRES_DB=drive_test \
  -p 5433:5432 -d postgis/postgis:15-3.3
```

### 2. Backend (FastAPI)
Navigate to `/backend`:
1. **Install Dependencies**: `pip install -r requirements.txt`
2. **Initialize Admin**: `python init_admin.py`  
   *Default: `admin@senzor.com` / `Senzor2026`*
3. **Start Server**: `uvicorn main:app --port 8000 --reload`
4. **Access UI**: Visit `http://localhost:8000/`

### 3. Mobile App (Flutter)
Navigate to `/mobile_app`:
1. **Configure IP**: Update `baseUrl` in `lib/services/sync_service.dart` to your local machine's IP (e.g., `http://192.168.1.5:8000/api/v1`).
2. **Run**: `flutter run`

---

## 🔗 Platform Map (Web Views)

| View | Purpose | Access |
|---|---|---|
| **Live Map** | Real-time signal overlay | `/` |
| **Analytics** | Signal distribution & ML metrics | `/view/analytics` |
| **Ledger** | Raw data stream | `/view/data` |
| **Simulator** | Synthetic data generation | `/view/simulate` |
| **Admin** | User & System management | `/view/admin` |
| **Login/Reg** | Authentication portal | `/view/login` |

---

## 📡 Signal Standards (3GPP Reference)

The system color-codes metrics according to industry-standard thresholds:

- **Excellent (>-80 RSRP)**: 🟢 High-speed data and stable voice.
- **Good (-80 to -90 RSRP)**: 🟡 Reliable coverage for most services.
- **Fair (-90 to -110 RSRP)**: 🟠 Service likely to be intermittent.
- **Poor (<-110 RSRP)**: 🔴 Coverage hole; data session failures expected.

---

## ☁️ Deployment Guides
- **[Cloud Deployment (VPS)](DEPLOYMENT.md)**: DigitalOcean/AWS/GCP instructions.
- **[Free Tier Deployment (Render/Supabase)](FREE_HOSTING.md)**: Zero-cost cloud hosting setup.
