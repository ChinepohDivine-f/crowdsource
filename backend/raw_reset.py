import psycopg2
import os

# Database URL from database.py
DB_URL = "postgresql://user:password@localhost:5433/drive_test"

print(f"Resetting database {DB_URL} via raw SQL...")
try:
    conn = psycopg2.connect(DB_URL)
    conn.autocommit = True
    cur = conn.cursor()
    
    # Drop existing tables
    cur.execute("DROP TABLE IF EXISTS core_networkmeasurement CASCADE")
    cur.execute("DROP TABLE IF EXISTS core_deviceprofile CASCADE")
    cur.execute("DROP TABLE IF EXISTS core_user CASCADE")
    print("Tables dropped.")
    
    conn.close()
    print("Reset complete. The app will recreate tables on next launch.")
except Exception as e:
    print(f"Error: {e}")
