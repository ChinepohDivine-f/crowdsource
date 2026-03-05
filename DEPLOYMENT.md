# 🚀 Deployment Guide

This guide explains how to deploy the Crowdsensed Drive Test Application (Backend & Database) to a production server.

## 🏗 Architecture
The deployment consists of two Docker containers:
1.  **Database**: PostGIS (PostgreSQL with spatial extensions).
2.  **Backend**: FastAPI application serving the API and Web Dashboard.

They are orchestrated using `docker-compose`.

---

## ☁️ Deploying to a VPS (DigitalOcean, AWS, Linode)

### Prerequisites
- A Linux server (Ubuntu 20.04/22.04 recommended).
- **Docker** and **Docker Compose** installed on the server.
- **Git** installed.

### Step-by-Step Instructions

#### 1. Clone the Repository
SSH into your server and clone your project:
```bash
git clone <your-repo-url>
cd crowdsource
```

#### 2. Configure Environment (Optional but Recommended)
For production, you should ideally change the default passwords.
- Open `docker-compose.yml` and update `POSTGRES_PASSWORD`.
- Note: If you change the password, update the `DATABASE_URL` in the `backend` service section of `docker-compose.yml` to match.

#### 3. Start the Services
Run the following command to build and start the containers in the background:
```bash
docker-compose up -d --build
```
- `--build`: Forces a rebuild of the backend image to ensure latest code.
- `-d`: Detached mode (runs in background).

#### 4. Verify Deployment
Check if containers are running:
```bash
docker ps
```
You should see `crowdsource_db` and `crowdsource_backend`.

- **Access the Dashboard**: Open your browser and go to `http://<your-server-ip>:8000`.
- **Access the API Docs**: Go to `http://<your-server-ip>:8000/docs`.

---

## 🌍 Connecting the Mobile App
Once your backend is live on a public IP:

1.  Open the Flutter project locally.
2.  Navigate to `lib/services/sync_service.dart`.
3.  Update the `apiUrl` with your **Server's Public IP**:
    ```dart
    final String apiUrl = "http://<YOUR-SERVER-IP>:8000/measurements/";
    ```
4.  Rebuild and deploy the app to your phone (`flutter run --release`).

---

## 🧹 Maintenance

**View Logs:**
```bash
docker-compose logs -f backend
```

**Stop Services:**
```bash
docker-compose down
```

**Update Code:**
```bash
git pull
docker-compose up -d --build
```
