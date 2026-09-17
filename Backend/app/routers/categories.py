from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.scrap_category import ScrapCategory
from sqlalchemy import func
from app.models.scrap_listing import ScrapListing, ListingStatus


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


@router.get("/stats/overview")
async def get_category_stats(db: Session = Depends(get_db)):
    """
    Get category statistics across all active listings
    
    - Public endpoint
    - Shows listing count and price range per category
    """
    print(f"\n Fetching category statistics...")
    
    categories = db.query(ScrapCategory).all()
    stats = []
    
    for category in categories:
        listings = db.query(ScrapListing).filter(
            ScrapListing.category_id == category.id,
            ScrapListing.availability_status == ListingStatus.ACTIVE
        ).all()
        
        count = len(listings)
        if count == 0:
            continue
        
        prices = [float(l.asking_price) for l in listings if l.asking_price]
        
        stats.append({
            "category_id": str(category.id),
            "category_name": category.name,
            "listing_count": count,
            "min_price": min(prices) if prices else None,
            "max_price": max(prices) if prices else None,
            "avg_price": round(sum(prices) / len(prices), 2) if prices else None
        })
    
    stats.sort(key=lambda x: x["listing_count"], reverse=True)
    
    print(f" Stats for {len(stats)} categories")
    
    return {
        "categories": stats,
        "total_active_listings": sum(s["listing_count"] for s in stats)
    }