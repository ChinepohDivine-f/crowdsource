# How to Run the Crowdsensed Drive Test Project

Follow these steps to get the entire system (Database, Backend, and Mobile App) running.

## 1. Database Setup
The backend requires a PostGIS database.
- **Using your existing DB**: Since you have a database running on port **5432**, ensure it has a database named `drive_test` and a user `user` with password `password`.
- **Note on PostGIS**: Make sure the **PostGIS extension** is enabled in your existing database:
  ```sql
  CREATE EXTENSION IF NOT EXISTS postgis;
  ```

## 2. Start the Backend API (FastAPI)
1. Open a new terminal and go to the `backend` folder:
   ```bash
   cd backend
   ```
2. Activate the Python virtual environment:
   ```bash
   source venv/bin/activate
   ```
3. Start the server using Uvicorn:
   ```bash
   uvicorn main:app --host 0.0.0.0 --port 8000
   ```
4. **View the Dashboard**: Open your browser and go to `http://localhost:8000/`. You should see the interactive map.

## 3. Start the Mobile App (Flutter)
1. Open a new terminal and go to the `mobile_app` folder:
   ```bash
   cd mobile_app
   ```
2. Ensure a phone (virtual or real) is connected:
   ```bash
   flutter devices
   ```
3. Run the app:
   ```bash
   flutter run
   ```

---

## 💡 Important Tips for Synchronization
- **Real Phone via WiFi**: If you are using a real Android phone instead of an emulator, you must update the `apiUrl` in `mobile_app/lib/services/sync_service.dart` to use your computer's **Local IP address** (e.g., `http://192.168.1.5:8000/measurements/`) instead of `localhost`.
- **Database Reset**: If you ever want to clear the backend database, run `docker-compose down -v` and then `docker-compose up -d`.
- **Swagger Docs**: You can test the API manually at `http://localhost:8000/docs`.

🏆 **Happy Drive Testing!**
