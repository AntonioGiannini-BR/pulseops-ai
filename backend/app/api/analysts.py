from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.api.deps import require_roles
from app.db.session import get_db

router = APIRouter(
    prefix="/analysts",
    tags=["Analistas"],
    dependencies=[Depends(require_roles("admin"))],
)


@router.get("/")
def list_analysts(db: Session = Depends(get_db)):
    result = db.execute(
        text("""
            SELECT id, email
            FROM app_users
            WHERE role = 'analista'
              AND is_active = TRUE
            ORDER BY email
        """)
    )

    return [dict(row) for row in result.mappings().all()]
