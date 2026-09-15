from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.scrap_category import ScrapCategory

router = APIRouter(prefix="/categories", tags=["Categories"])


@router.get("/")
async def get_categories(db: Session = Depends(get_db)):
    """
    Get all scrap categories
    
    - Public endpoint (no authentication required)
    - Returns all categories sorted alphabetically
    - Used for dropdowns in the frontend
    """
    print(f"\nFetching all categories...")
    
    categories = db.query(ScrapCategory).order_by(ScrapCategory.name).all()
    
    print(f"  Found {len(categories)} categories")
    
    return {
        "categories": [
            {
                "id": str(c.id),
                "name": c.name,
                "description": c.description,
                "parent_category_id": str(c.parent_category_id) if c.parent_category_id else None
            }
            for c in categories
        ],
        "total": len(categories)
    }


@router.get("/{category_id}")
async def get_category(
    category_id: str,
    db: Session = Depends(get_db)
):
    """Get a single category by ID"""
    import uuid
    
    try:
        category_uuid = uuid.UUID(category_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid category ID format"
        )
    
    category = db.query(ScrapCategory).filter(
        ScrapCategory.id == category_uuid
    ).first()
    
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found"
        )
    
    return {
        "id": str(category.id),
        "name": category.name,
        "description": category.description,
        "parent_category_id": str(category.parent_category_id) if category.parent_category_id else None
    }