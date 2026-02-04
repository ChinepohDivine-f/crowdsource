# ☁️ Free Hosting Guide (Supabase + Render)

This guide explains how to host your **Crowdsensed Drive Test Application** for **FREE** using a combination of **Supabase** (for the Database) and **Render** (for the Backend API).

## 🚀 Overview

| Component | Service | Tier | Notes |
| :--- | :--- | :--- | :--- |
| **Database** | [Supabase](https://supabase.com) | **Free Forever** | 500MB storage, supports PostGIS via extension. |
| **Backend** | [Render](https://render.com) | **Free** | Spins down after inactivity (15 mins), HTTPS included. |
Senzor@2026
---

## 🛠 Part 1: Set up the Database (Supabase)

Supabase provides a managed PostgreSQL database that is perfect for this project.

1.  **Create an Account**: Go to [supabase.com](https://supabase.com) and sign up/login with GitHub.
2.  **New Project**:
    *   Click **"New Project"**.
    *   Choose an Organization.
    *   Name: `crowdsource-db`.
    *   Database Password: **GENERATE A STRONG PASSWORD AND SAVE IT!** You will need this later.
    *   Region: Choose one close to you (e.g., EU West, US East).
    *   Click **"Create new project"**.
3.  **Enable PostGIS**:
    *   Wait for the project to provision (takes ~2 mins).
    *   Go to the **"SQL Editor"** (icon on the left sidebar).
    *   Click **"New Query"**.
    *   Run the following command:
        ```sql
        CREATE EXTENSION postgis;
        ```
    *   Click **Run**. You should see "Success".
4.  **Get Connection String**:
    *   Go to **Project Settings** (gear icon) -> **Database**.
    *   Under **Connection Parameters**, look for "URI" or "Connection String".
    *   It will look like this: `postgresql://postgres:[YOUR-PASSWORD]@db.xxxx.supabase.co:5432/postgres`
    *   **Action**: Copy this string and replace `[YOUR-PASSWORD]` with the password you created in step 2. **Keep this safe.**
postgresql://postgres:Senzor@2026@db.prbxscjomajvkpaipuiy.supabase.co:5432/postgres
---

## 🖥 Part 2: Deploy the Backend (Render)

Render will build and run your Docker container from your GitHub repository.

### Prerequisites
*   Ensure your project is pushed to a **GitHub Repository**.

### Steps
1.  **Create an Account**: Go to [render.com](https://render.com) and sign up with GitHub.
2.  **New Web Service**:
    *   Click **"New +"** -> **"Web Service"**.
    *   Connect your GitHub repository (`crowdsource`).
3.  **Configure Service**:
    *   **Name**: `crowdsource-backend`
    *   **Region**: Same as (or close to) your Supabase region.
    *   **Branch**: `main` (or master).
    *   **Root Directory**: `backend` (Important! This tells Render where the Dockerfile is).
    *   **Runtime**: **Docker**.
    *   **Instance Type**: **Free**.
4.  **Environment Variables**:
    *   Scroll down to "Environment Variables".
    *   Click **"Add Environment Variable"**.
    *   **Key**: `DATABASE_URL`
    *   **Value**: Paste your Supabase connection string from Part 1.
    *   *Note: Ensure `python-multipart` is in your `backend/requirements.txt` (it is required for OAuth2 flow).*
5.  **Deploy**:
    *   Click **"Create Web Service"**.
    *   Render will start building your Docker image. This may take 5-10 minutes.
    *   Once complete, you will see a green "Live" badge and a URL like `https://crowdsource-backend.onrender.com`.

---

## 📱 Part 3: Connect Mobile App

Now that your backend is live with HTTPS, connect your mobile app.

1.  Open `mobile_app/lib/services/sync_service.dart`.
2.  Update the `baseUrl` variable:
    ```dart
    // Replace with your Render URL (no trailing slash)
    final String baseUrl = "https://crowdsource-backend.onrender.com";
    ```
3.  **Build Release**:
    ```bash
    flutter run --release
    ```

---

## ✅ Summary

*   Your **Database** is hosted on Supabase (Free).
*   Your **Backend** is hosted on Render (Free).
*   Your **Mobile App** syncs data securely over HTTPS.

**Note:** On the free tier, Render spins down your service after 15 minutes of inactivity. The first request after a break might take ~30-50 seconds to respond. This is normal behavior for free hosting.
