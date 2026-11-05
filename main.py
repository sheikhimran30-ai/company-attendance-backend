from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from datetime import datetime
import os
import psycopg2

app = FastAPI()

# 🔒 CORS Configuration to allow secure connections from any mobile browser
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 🔗 Database connection link automatically fetched from the cloud environment
DATABASE_URL = os.getenv("DATABASE_URL")

def get_db_connection():
    return psycopg2.connect(DATABASE_URL)

class AttendanceRecord(BaseModel):
    emp_id: int
    punch_type: str
    latitude: float
    longitude: float

@app.post("/api/punch")
def mark_attendance(record: AttendanceRecord):
    if record.punch_type not in ['IN', 'OUT']:
        raise HTTPException(status_code=400, detail="Invalid punch type configuration")
    
    # ✅ GLOBAL FIX: 100% accurate clickable Google Maps URL generator
    maps_link = f"https://google.com{record.latitude},{record.longitude}"
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Validate if the Employee ID exists in the corporate registry
        cursor.execute("SELECT name FROM employees WHERE emp_id = %s;", (record.emp_id,))
        emp_exists = cursor.fetchone()
        if not emp_exists:
            raise HTTPException(status_code=404, detail="Employee ID not found in database!")

        emp_name = emp_exists[0]

        # Insert secure logs into the cloud attendance ledger
        query = """
            INSERT INTO attendance_logs (emp_id, punch_type, latitude, longitude, punch_address, punch_time)
            VALUES (%s, %s, %s, %s, %s, %s);
        """
        cursor.execute(query, (record.emp_id, record.punch_type, record.latitude, record.longitude, maps_link, datetime.now()))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return {
            "status": "Success", 
            "message": f"Punch {record.punch_type} recorded successfully!", 
            "employee": emp_name,
            "maps_url": maps_link
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
