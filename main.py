from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from datetime import datetime
import os
import psycopg2

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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
        raise HTTPException(status_code=400, detail="Invalid punch configuration token")

    maps_link = f"https://www.google.com/maps?q={record.latitude},{record.longitude}"

    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT name FROM public.employees WHERE emp_id = %s;", (record.emp_id,))
        emp_exists = cursor.fetchone()
        if not emp_exists:
            raise HTTPException(status_code=404, detail="Employee configuration not found")

        emp_name = str(emp_exists[0])

        query = """
            INSERT INTO public.attendance_logs (emp_id, punch_type, latitude, longitude, punch_address, punch_time)
            VALUES (%s, %s, %s, %s, %s, %s);
        """
        cursor.execute(query, (record.emp_id, record.punch_type, record.latitude, record.longitude, maps_link, datetime.now()))

        conn.commit()
        cursor.close()

        return {
            "status": "Success",
            "message": f"Punch {record.punch_type} recorded dynamically",
            "employee": emp_name,
            "maps_url": maps_link
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if conn:
            conn.close()
