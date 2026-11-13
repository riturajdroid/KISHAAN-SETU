"""
FastAPI Backend - Contact Form Response Handler
================================================
Functionality: Receives contact form responses and stores them in XAMPP MySQL.
"""

import os
from datetime import datetime
from typing import Optional
from pathlib import Path

from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, text
from sqlalchemy.orm import declarative_base, sessionmaker, Session

BASE_DIR = Path(__file__).resolve().parent

# ==============================================================================
# SQL DATABASE CONFIGURATION (XAMPP MySQL)
# ==============================================================================
MYSQL_USER = os.getenv("DB_USER", "root")
MYSQL_PASSWORD = os.getenv("DB_PASSWORD", "")
MYSQL_HOST = os.getenv("DB_HOST", "localhost")
MYSQL_PORT = os.getenv("DB_PORT", "3306")
MYSQL_DATABASE = os.getenv("DB_NAME", "contact_db")

MYSQL_ROOT_URL = f"mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_HOST}:{MYSQL_PORT}"
MYSQL_APP_URL = f"{MYSQL_ROOT_URL}/{MYSQL_DATABASE}"
SQLITE_FALLBACK_URL = f"sqlite:///{BASE_DIR / 'contacts.db'}"

engine = None

try:
    # 1. Connect to MySQL server in XAMPP and create database if it doesn't exist
    root_engine = create_engine(MYSQL_ROOT_URL, connect_args={"connect_timeout": 3})
    with root_engine.connect() as conn:
        conn.execute(text(f"CREATE DATABASE IF NOT EXISTS `{MYSQL_DATABASE}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"))
        conn.commit()

    # 2. Connect to the contact_db database
    engine = create_engine(MYSQL_APP_URL, pool_pre_ping=True)
    with engine.connect() as conn:
        conn.execute(text("SELECT 1"))
    print(f" [DB] Connected to XAMPP MySQL (Database: {MYSQL_DATABASE})")

except Exception as err:
    print(f" [DB NOTICE] Could not connect to XAMPP MySQL: {err}")
    print(f" [DB NOTICE] Falling back to local SQLite database (contacts.db).")
    print(f" [DB NOTICE] Start MySQL in XAMPP Control Panel to use XAMPP.")
    engine = create_engine(SQLITE_FALLBACK_URL, connect_args={"check_same_thread": False})

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


# ==============================================================================
# DATABASE MODEL
# ==============================================================================
class ContactSubmission(Base):
    __tablename__ = "contacts"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    email = Column(String(120), nullable=False)
    phone = Column(String(25), nullable=True)
    subject = Column(String(200), nullable=False)
    message = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


# Auto-create the table
Base.metadata.create_all(bind=engine)


# ==============================================================================
# FORM INPUT SCHEMA
# ==============================================================================
class ContactFormRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    email: str = Field(..., pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
    phone: Optional[str] = Field(None, max_length=25)
    subject: str = Field(..., min_length=3, max_length=200)
    message: str = Field(..., min_length=5, max_length=5000)


# ==============================================================================
# FASTAPI APPLICATION
# ==============================================================================
app = FastAPI(title="Contact Form Backend", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ==============================================================================
# SOLE BACKEND FUNCTIONALITY: GETTING THE FORM RESPONSE
# ==============================================================================
@app.post("/api/contact", status_code=status.HTTP_201_CREATED)
def receive_form_response(payload: ContactFormRequest):
    """Receives contact form input from the user and saves it to the SQL database."""
    db: Session = SessionLocal()
    try:
        entry = ContactSubmission(
            name=payload.name.strip(),
            email=payload.email.strip().lower(),
            phone=payload.phone.strip() if payload.phone else None,
            subject=payload.subject.strip(),
            message=payload.message.strip(),
            created_at=datetime.utcnow()
        )
        db.add(entry)
        db.commit()
        db.refresh(entry)

        return {
            "success": True,
            "message": f"Thank you {entry.name}, your response has been recorded successfully!",
            "id": entry.id
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error while saving response: {str(e)}"
        )
    finally:
        db.close()


# Static file routes to serve the page directly
@app.get("/")
def serve_index():
    return FileResponse(BASE_DIR / "index.html")


@app.get("/style.css")
def serve_css():
    return FileResponse(BASE_DIR / "style.css", media_type="text/css")


@app.get("/script.js")
def serve_js():
    return FileResponse(BASE_DIR / "script.js", media_type="application/javascript")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
