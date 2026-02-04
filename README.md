# Senzor: Crowdsensed Drive Test Platform

A professional Mobile-to-Cloud crowdsensing system designed for cellular network monitoring and analysis. This platform allows for real-time capture of network metrics like RSRP and SINR, coupled with GPS data, to identify coverage holes and optimize network performance.

## 🌟 Features

-   **Real-time Data Collection**: Captures signal strength (RSRP), signal quality (SINR), network type, and cell ID.
-   **GPS Integration**: Automatically tags every measurement with high-precision GPS coordinates.
-   **Interactive Map**: Visualizes collected data points on an OpenStreetMap with color-coded markers (Red for coverage holes, Green for good signal).
-   **Automated Sync**: Periodically synchronizes local data with a central cloud database.
-   **Analytics**: Backend logic to identify "Coverage Holes" where signal strength drops below functional thresholds.

## 🏗 How it was Made (Architecture)

The system is built using a modern, scalable architecture:

1.  **Mobile Client (Flutter)**: A cross-platform app that interfaces with device sensors and telephony APIs to gather raw network data.
2.  **Backend API (FastAPI)**: A high-performance Python backend that handles data ingestion, processing, and spatial analytics.
3.  **Spatial Database (PostGIS)**: An extension of PostgreSQL that adds support for geographic objects, allowing for complex spatial queries.
4.  **Containerization (Docker)**: The entire infrastructure is orchestrated using Docker for consistent and reliable deployment.

---

## 🚀 Quick Start (Setup Everything)

### Prerequisites
- [Docker](https://docs.docker.com/get-docker/) installed.
- [Flutter SDK](https://docs.flutter.dev/get-started/install) installed.
- [Python 3.9+](https://www.python.org/downloads/) installed.

### Step 1: Start the Database (Docker)
We use **PostGIS** for spatial data storage. Run the following command to start the container:

```bash
docker run --name crowdsource_db \
  -e POSTGRES_USER=user \
  -e POSTGRES_PASSWORD=password \
  -e POSTGRES_DB=drive_test \
  -p 5433:5432 -d postgis/postgis:15-3.3
```

### Step 2: Start the Backend (FastAPI)
1.  Navigate to the backend folder: `cd backend`
2.  Create and activate a virtual environment:
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```
3.  Install dependencies: `pip install -r requirements.txt`
4.  Run the server: `uvicorn main:app --host 0.0.0.0 --port 8000 --reload`

### Step 3: Run the Mobile App (Flutter)
1.  Navigate to the mobile folder: `cd mobile_app`
2.  **Configuration**: Update your Local IP address in `lib/services/sync_service.dart` to point to the FastAPI server.
3.  Install dependencies: `flutter pub get`
4.  Run the app: `flutter run`

---

---

## ☁️ Deployment

Want to run this properly on a server?
- **[Standard Deployment Guide (VPS)](DEPLOYMENT.md)** - For DigitalOcean, AWS, etc.
- **[Free Hosting Guide (Zero Cost)](FREE_HOSTING.md)** - Using Supabase and Render.

---

## 🗄 Database Access

You can access the PostGIS database directly to inspect the raw measurements.

### Connection Details
- **Host**: `localhost` (or your Docker IP)
- **Port**: `5433`
- **User**: `user`
- **Password**: `password`
- **Database**: `drive_test`

### Access via Command Line (psql)
If you have `psql` installed, run:
```bash
PGPASSWORD=password psql -h localhost -p 5433 -U user -d drive_test
```

### Recommended GUI Tools
For a better visual experience, we recommend using one of these tools:
- **[DBeaver](https://dbeaver.io/)**: (Free/Open Source) Supports PostGIS spatial data visualization.
- **[TablePlus](https://tableplus.com/)**: (Shareware) Fast and lightweight.
- **[pgAdmin](https://www.pgadmin.org/)**: (Free) The official Postgres management tool.

---

## 📡 Key Metrics Explained
-   **RSRP (Reference Signal Received Power)**: Indicates the signal strength. Values lower than **-110 dBm** are typically flagged as coverage holes.
-   **SINR (Signal-to-Interference-plus-Noise Ratio)**: Measures the quality of the signal. Higher values indicate a cleaner, more reliable connection.
