from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.db.session import get_db

router = APIRouter(prefix="/tickets", tags=["Tickets"])


@router.get("/")
def list_tickets(db: Session = Depends(get_db)):
    result = db.execute(
        text("""
            SELECT
                id,
                title,
                description,
                priority,
                status,
                requester_id,
                category_id,
                opened_at
            FROM tickets
            ORDER BY id
        """)
    )

    return [dict(row) for row in result.mappings().all()]
