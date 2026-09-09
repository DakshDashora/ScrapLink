from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import desc, asc
from typing import Optional
import uuid

from app.database import get_db
from app.models.user import User
from app.models.scrap_listing import ScrapListing, ListingStatus, ListingUnit
from app.models.organization_member import OrganizationMember
from app.models.scrap_category import ScrapCategory
from app.models.organization import Organization
from app.security import get_current_user
from app.schemas.scrap_listing import (
    ListingCreate, ListingUpdate, ListingResponse,
    ListingListResponse
)

router = APIRouter(prefix="/listings", tags=["Listings"])


# ============================================
# HELPER FUNCTIONS
# ============================================

def check_listing_owner(listing: ScrapListing, user_id: str, db: Session) -> bool:
    """Check if user is a member of the listing's organization"""
    member = db.query(OrganizationMember).filter(
        OrganizationMember.user_id == uuid.UUID(user_id),
        OrganizationMember.organization_id == listing.seller_org_id
    ).first()
    return member is not None


def build_listing_response(listing: ScrapListing) -> dict:
    """Build response dict from listing object"""
    return {
        "id": str(listing.id),
        "seller_org_id": str(listing.seller_org_id),
        "seller_org_name": listing.seller_org.name if listing.seller_org else "Unknown",
        "category_id": str(listing.category_id),
        "category_name": listing.category.name if listing.category else "Unknown",
        "material_name": listing.material_name,
        "grade": listing.grade,
        "description": listing.description,
        "quantity": str(listing.quantity),
        "unit": listing.unit.value,
        "asking_price": str(listing.asking_price) if listing.asking_price else None,
        "location": listing.location,
        "availability_status": listing.availability_status.value,
        "created_at": listing.created_at.isoformat() if listing.created_at else None,
        "updated_at": listing.updated_at.isoformat() if listing.updated_at else None,
        "media": []
    }


# ============================================
# API ENDPOINTS
# ============================================

@router.post("/", response_model=ListingResponse, status_code=status.HTTP_201_CREATED)
async def create_listing(
    listing_data: ListingCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Create a new scrap listing
    
    - Seller must be a member of an organization
    - Category must exist
    """
    
    print(f"\n📝 Creating listing for user: {current_user.email}")
    
    # 1. Get user's organization
    org_member = db.query(OrganizationMember).filter(
        OrganizationMember.user_id == current_user.id
    ).first()
    
    if not org_member:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User is not a member of any organization. Please create an organization first."
        )
    
    print(f"✅ User is member of organization: {org_member.organization_id}")
    
    # 2. Verify category exists
    category = db.query(ScrapCategory).filter(
        ScrapCategory.id == uuid.UUID(listing_data.category_id)
    ).first()
    
    if not category:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid category ID"
        )
    
    print(f"✅ Category found: {category.name}")
    
    # 3. Create listing
    try:
        listing = ScrapListing(
            id=uuid.uuid4(),
            seller_org_id=org_member.organization_id,
            category_id=uuid.UUID(listing_data.category_id),
            material_name=listing_data.material_name,
            grade=listing_data.grade,
            description=listing_data.description,
            quantity=listing_data.quantity,
            unit=listing_data.unit,
            asking_price=listing_data.asking_price,
            location=listing_data.location,
            availability_status=ListingStatus.ACTIVE
        )
        
        db.add(listing)
        db.commit()
        db.refresh(listing)
        
        print(f"✅ Listing created with ID: {listing.id}")
        
        # Reload with relationships
        listing = db.query(ScrapListing).options(
            joinedload(ScrapListing.seller_org),
            joinedload(ScrapListing.category)
        ).filter(ScrapListing.id == listing.id).first()
        
        return build_listing_response(listing)
        
    except Exception as e:
        db.rollback()
        print(f"❌ Error creating listing: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error creating listing: {str(e)}"
        )


@router.get("/", response_model=ListingListResponse)
async def get_listings(
    # Filter parameters
    category_id: Optional[str] = Query(None, description="Filter by category ID"),
    material_name: Optional[str] = Query(None, description="Filter by material name (partial match)"),
    min_price: Optional[float] = Query(None, description="Minimum asking price"),
    max_price: Optional[float] = Query(None, description="Maximum asking price"),
    min_quantity: Optional[float] = Query(None, description="Minimum quantity"),
    max_quantity: Optional[float] = Query(None, description="Maximum quantity"),
    unit: Optional[ListingUnit] = Query(None, description="Unit (kg, tonne, unit, etc.)"),
    status: Optional[ListingStatus] = Query(ListingStatus.ACTIVE, description="Listing status"),
    
    # Location filter
    latitude: Optional[float] = Query(None, description="Latitude for location search"),
    longitude: Optional[float] = Query(None, description="Longitude for location search"),
    radius_km: Optional[float] = Query(10.0, description="Search radius in km"),
    
    # Pagination
    page: int = Query(1, ge=1, description="Page number (starts at 1)"),
    size: int = Query(20, ge=1, le=100, description="Items per page (max 100)"),
    
    # Sorting
    sort_by: str = Query("created_at", description="Sort field (created_at, asking_price, quantity)"),
    sort_order: str = Query("desc", description="Sort order (asc, desc)"),
    
    db: Session = Depends(get_db)
    # ✅ No current_user - this is PUBLIC!
):
    """
    Get listings with search and filters
    
    Features:
    - Public endpoint (no authentication required for browsing)
    - Only active listings are shown by default
    - Supports pagination, sorting, and multiple filters
    - Partial text search on material name
    - Price and quantity range filters
    """
    
    print(f"\n🔍 Searching listings...")
    print(f"   Filters: category={category_id}, material={material_name}")
    print(f"   Page: {page}, Size: {size}")
    
    # Build query
    query = db.query(ScrapListing).options(
        joinedload(ScrapListing.seller_org),
        joinedload(ScrapListing.category)
    )
    
    # Filter by status (default: ACTIVE)
    if status:
        query = query.filter(ScrapListing.availability_status == status)
    else:
        query = query.filter(ScrapListing.availability_status == ListingStatus.ACTIVE)
    
    # Filter by category
    if category_id:
        try:
            query = query.filter(ScrapListing.category_id == uuid.UUID(category_id))
            print(f"   ✅ Filtering by category: {category_id}")
        except ValueError:
            print(f"   ❌ Invalid category ID: {category_id}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid category ID format"
            )
    
    # Filter by material name (partial match - case insensitive)
    if material_name:
        query = query.filter(ScrapListing.material_name.ilike(f"%{material_name}%"))
        print(f"   ✅ Filtering by material: {material_name}")
    
    # Filter by price range
    if min_price is not None:
        query = query.filter(ScrapListing.asking_price >= min_price)
        print(f"   ✅ Filtering by min price: {min_price}")
    if max_price is not None:
        query = query.filter(ScrapListing.asking_price <= max_price)
        print(f"   ✅ Filtering by max price: {max_price}")
    
    # Filter by quantity range
    if min_quantity is not None:
        query = query.filter(ScrapListing.quantity >= min_quantity)
    if max_quantity is not None:
        query = query.filter(ScrapListing.quantity <= max_quantity)
    
    # Filter by unit
    if unit:
        query = query.filter(ScrapListing.unit == unit)
        print(f"   ✅ Filtering by unit: {unit}")
    
    # Location-based filtering (simplified for now)
    if latitude and longitude:
        print(f"   📍 Location filter: lat={latitude}, lon={longitude}, radius={radius_km}km")
    
    # Count total before pagination
    total = query.count()
    print(f"   📊 Total matching listings: {total}")
    
    # Sorting
    if sort_by == "created_at":
        order_col = ScrapListing.created_at
    elif sort_by == "asking_price":
        order_col = ScrapListing.asking_price
    elif sort_by == "quantity":
        order_col = ScrapListing.quantity
    else:
        order_col = ScrapListing.created_at
    
    if sort_order.lower() == "asc":
        query = query.order_by(asc(order_col))
    else:
        query = query.order_by(desc(order_col))
    
    # Pagination
    offset = (page - 1) * size
    query = query.offset(offset).limit(size)
    
    listings = query.all()
    print(f"   ✅ Retrieved {len(listings)} listings for page {page}")
    
    # Build response
    items = [build_listing_response(l) for l in listings]
    pages = (total + size - 1) // size if total > 0 else 0
    
    return ListingListResponse(
        items=items,
        total=total,
        page=page,
        size=size,
        pages=pages
    )


@router.get("/my-listings", response_model=ListingListResponse)
async def get_my_listings(
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(20, ge=1, le=100, description="Items per page"),
    status: Optional[ListingStatus] = Query(None, description="Filter by status"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get listings for the current user's organization(s)
    
    Features:
    - Requires authentication
    - Returns all listings from organizations the user belongs to
    - Supports pagination and status filtering
    """
    
    print(f"\n📋 Fetching my listings for user: {current_user.email}")
    
    # Get user's organizations
    org_memberships = db.query(OrganizationMember).filter(
        OrganizationMember.user_id == current_user.id
    ).all()
    
    if not org_memberships:
        print(f"   ⚠️ User is not a member of any organization")
        return ListingListResponse(
            items=[],
            total=0,
            page=page,
            size=size,
            pages=0
        )
    
    org_ids = [m.organization_id for m in org_memberships]
    print(f"   ✅ User belongs to {len(org_ids)} organization(s)")
    
    # Build query
    query = db.query(ScrapListing).options(
        joinedload(ScrapListing.seller_org),
        joinedload(ScrapListing.category)
    ).filter(ScrapListing.seller_org_id.in_(org_ids))
    
    # Filter by status if provided
    if status:
        query = query.filter(ScrapListing.availability_status == status)
        print(f"   ✅ Filtering by status: {status.value}")
    
    # Count total
    total = query.count()
    print(f"   📊 Total listings: {total}")
    
    # Pagination
    offset = (page - 1) * size
    listings = query.order_by(desc(ScrapListing.created_at)).offset(offset).limit(size).all()
    
    items = [build_listing_response(l) for l in listings]
    pages = (total + size - 1) // size if total > 0 else 0
    
    print(f"   ✅ Retrieved {len(listings)} listings for page {page}")
    
    return ListingListResponse(
        items=items,
        total=total,
        page=page,
        size=size,
        pages=pages
    )


@router.get("/{listing_id}", response_model=ListingResponse)
async def get_listing(
    listing_id: str,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user)
):
    """
    Get a single listing by ID
    
    - Public for active listings
    - Requires auth for inactive listings
    """
    
    print(f"\n📋 Fetching listing: {listing_id}")
    
    listing = db.query(ScrapListing).options(
        joinedload(ScrapListing.seller_org),
        joinedload(ScrapListing.category)
    ).filter(ScrapListing.id == uuid.UUID(listing_id)).first()
    
    if not listing:
        print(f"❌ Listing not found: {listing_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Listing not found"
        )
    
    print(f"✅ Listing found: {listing.material_name}")
    
    # Check access for inactive listings
    if listing.availability_status != ListingStatus.ACTIVE:
        print(f"⚠️ Listing is {listing.availability_status.value}, checking access...")
        if not current_user:
            print(f"❌ No user authenticated")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required to view this listing"
            )
        if not check_listing_owner(listing, str(current_user.id), db):
            print(f"❌ User is not owner")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have access to this listing"
            )
        print(f"✅ User is owner, access granted")
    
    return build_listing_response(listing)


@router.put("/{listing_id}", response_model=ListingResponse)
async def update_listing(
    listing_id: str,
    listing_data: ListingUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Update a listing
    
    - Only the seller can update their listing
    """
    
    print(f"\n✏️ Updating listing: {listing_id}")
    print(f"User: {current_user.email}")
    
    listing = db.query(ScrapListing).filter(
        ScrapListing.id == uuid.UUID(listing_id)
    ).first()
    
    if not listing:
        print(f"❌ Listing not found: {listing_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Listing not found"
        )
    
    print(f"✅ Listing found: {listing.material_name}")
    
    # Check ownership
    if not check_listing_owner(listing, str(current_user.id), db):
        print(f"❌ User is not owner")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to update this listing"
        )
    
    print(f"✅ User is owner, updating...")
    
    # Update fields
    try:
        update_data = listing_data.dict(exclude_unset=True)
        print(f"📝 Updating fields: {list(update_data.keys())}")
        
        # Handle category_id specially
        if "category_id" in update_data and update_data["category_id"]:
            category = db.query(ScrapCategory).filter(
                ScrapCategory.id == uuid.UUID(update_data["category_id"])
            ).first()
            if not category:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid category ID"
                )
            listing.category_id = uuid.UUID(update_data["category_id"])
            del update_data["category_id"]
        
        # Update other fields
        for field, value in update_data.items():
            if value is not None:
                setattr(listing, field, value)
        
        db.commit()
        db.refresh(listing)
        print(f"✅ Listing updated successfully")
        
        # Reload with relationships
        listing = db.query(ScrapListing).options(
            joinedload(ScrapListing.seller_org),
            joinedload(ScrapListing.category)
        ).filter(ScrapListing.id == listing.id).first()
        
        return build_listing_response(listing)
        
    except Exception as e:
        db.rollback()
        print(f"❌ Error updating listing: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error updating listing: {str(e)}"
        )


@router.delete("/{listing_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_listing(
    listing_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Delete a listing (soft delete - sets status to CLOSED)
    
    - Only the seller can delete their listing
    """
    
    print(f"\n🗑️ Deleting listing: {listing_id}")
    print(f"User: {current_user.email}")
    
    listing = db.query(ScrapListing).filter(
        ScrapListing.id == uuid.UUID(listing_id)
    ).first()
    
    if not listing:
        print(f"❌ Listing not found: {listing_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Listing not found"
        )
    
    print(f"✅ Listing found: {listing.material_name}")
    
    # Check ownership
    if not check_listing_owner(listing, str(current_user.id), db):
        print(f"❌ User is not owner")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to delete this listing"
        )
    
    # Soft delete - set status to CLOSED
    listing.availability_status = ListingStatus.CLOSED
    db.commit()
    
    print(f"✅ Listing closed successfully")
    
    return None