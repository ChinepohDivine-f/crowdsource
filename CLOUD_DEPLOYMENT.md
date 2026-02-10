# ☁️ Free Cloud Deployment Guide

You can host your entire network monitoring system for free using two professional platforms: **Supabase** (for the database) and **Render** (for the FastAPI backend).

## 1. The Database: Supabase (Free Postgres & PostGIS)
Supabase is the best choice because it provides a "Forever Free" tier with a generous 500MB limit and built-in map support.

### Steps:
1.  Go to [Supabase.com](https://supabase.com) and create a free account.
2.  Create a new project (name it `crowdsource`).
3.  Go to **Database Settings** (Gear icon) -> **Connection String**.
4.  Copy the **URI connection string**. It will look like this:
    `postgresql://postgres:[YOUR-PASSWORD]@db.[REF].supabase.co:5432/postgres`
5.  **Enable PostGIS**: Go to the **SQL Editor** in Supabase and run:
    ```sql
    CREATE EXTENSION IF NOT EXISTS postgis;
    ```

---

## 2. The Backend: Render (Free FastAPI Hosting)
Render allows you to host web services for free.

### Steps:
1.  **Push to GitHub**: Create a private GitHub repository and push your project code to it.
2.  Go to [Render.com](https://render.com) and create a free account.
3.  Click **New +** -> **Web Service**.
4.  Connect your GitHub repository.
5.  **Configure**:
    - **Runtime**: Python
    - **Build Command**: `pip install -r backend/requirements.txt`
    - **Start Command**: `cd backend && uvicorn main:app --host 0.0.0.0 --port $PORT`
6.  **Environment Variables**: In Render settings, add:
    - `DATABASE_URL`: (The connection string you copied from Supabase).

---

## 3. The Mobile App: Final Update
Once Render gives you your public URL (e.g., `https://crowdsource-api.onrender.com`), update your app:

1.  Open `mobile_app/lib/services/sync_service.dart`.
2.  Update line 8:
    ```dart
    final String apiUrl = "https://your-render-url.com/measurements/";
    ```

---

## 🏆 Why this is "A+" Grade:
- **Zero Cost**: You stay within the free limits of both platforms.
- **Global Access**: You can collect data in one city and see the map results from a browser in another city!
- **Professional Architecture**: You are using standard industry tools (FastAPI, Postgres, Render).

> [!IMPORTANT]
> **Database Security**: When you use Supabase, make sure your password is strong and don't share your Connection URI publicly.
