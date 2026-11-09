from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db

router = APIRouter(
    prefix="/categories",
    tags=["Categorias"],
    dependencies=[Depends(get_current_user)],
)


@router.get("/")
def list_categories(db: Session = Depends(get_db)):
    result = db.execute(
        text("""
            SELECT id, name
            FROM categories
            WHERE is_active = TRUE
            ORDER BY name
        """)
    )

    return [dict(row) for row in result.mappings().all()]
