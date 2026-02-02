"""
Main FastAPI application for NCSAA Basketball Scheduling System.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import routes

app = FastAPI(
    title="NCSAA Basketball Scheduling API",
    description="API for generating and managing basketball game schedules",
    version="1.0.0"
)

# Enable CORS for frontend (allow any localhost origin so dev on any port works)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:3001",
        "http://127.0.0.1:3001",
    ],
    allow_origin_regex=r"^https?://(localhost|127\.0\.0\.1)(:\d+)?$",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
    max_age=600,
)

# Include API routes
app.include_router(routes.router)


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "NCSAA Basketball Scheduling API",
        "version": "1.0.0",
        "endpoints": {
            "generate": "/api/schedule",
            "stats": "/api/stats",
            "health": "/api/health"
        }
    }
