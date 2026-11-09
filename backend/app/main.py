from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI, HTTPException
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from app.api.tickets import router as tickets_router
from app.api.auth import router as auth_router
from app.db.session import engine
from app.api.ticket_comments import router as ticket_comments_router
from app.api.dashboard import router as dashboard_router
from app.api.categories import router as categories_router
from app.api.analysts import router as analysts_router
from app.api.ai_suggestions import router as ai_suggestions_router

app = FastAPI(
    title="PulseOps AI API",
    description="API de operações empresariais do PulseOps AI",
    version="0.2.0",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["Authorization", "Content-Type"],
)

app.include_router(tickets_router)
app.include_router(auth_router)
app.include_router(ticket_comments_router)
app.include_router(dashboard_router)
app.include_router(categories_router)
app.include_router(analysts_router)
app.include_router(ai_suggestions_router)

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
