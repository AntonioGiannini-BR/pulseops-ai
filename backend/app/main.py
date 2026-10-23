from fastapi import FastAPI, HTTPException
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from app.api.tickets import router as tickets_router
from app.api.auth import router as auth_router
from app.db.session import engine


app = FastAPI(
    title="PulseOps AI API",
    description="API de operações empresariais do PulseOps AI",
    version="0.2.0",
)
app.include_router(tickets_router)
app.include_router(auth_router)


@app.get("/health", tags=["Health"])
def health_check():
    return {
        "status": "ok",
        "service": "pulseops-ai-api",
        "version": "0.2.0",
    }


@app.get("/health/db", tags=["Health"])
def database_health():
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))

        return {
            "status": "ok",
            "database": "connected",
        }

    except SQLAlchemyError:
        raise HTTPException(
            status_code=503,
            detail="Database unavailable"
        )