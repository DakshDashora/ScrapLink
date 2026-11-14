from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.ml_reference import MLMaterial, MLScrapType

router = APIRouter(prefix="/api/ml-options", tags=["ML Dropdowns"])

@router.get("/materials")
async def get_materials(db: Session = Depends(get_db)):
    """Get list of trained materials for frontend dropdown"""
    materials = db.query(MLMaterial).all()
    return {"materials": [m.name for m in materials]}

@router.get("/scrap-types")
async def get_scrap_types(db: Session = Depends(get_db)):
    """Get list of trained scrap types for frontend dropdown"""
    scrap_types = db.query(MLScrapType).all()
    return {"scrap_types": [st.name for st in scrap_types]}