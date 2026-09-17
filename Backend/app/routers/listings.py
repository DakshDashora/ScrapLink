from fastapi import APIRouter, Depends, HTTPException, status, Query,UploadFile, File, Form
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import desc, asc
from typing import Optional
import uuid
import math
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
from app.models.listing_media import ListingMedia
from app.schemas.listing_media import MediaResponse, MediaUploadResponse, MediaListResponse
from app.utils.cloudinary_service import upload_image, delete_image
from typing import List


router = APIRouter(prefix="/listings", tags=["Listings"])



def check_listing_owner(listing: ScrapListing, user_id: str, db: Session) -> bool:
    """Check if user is a member of the listing's organization"""
    member = db.query(OrganizationMember).filter(
        OrganizationMember.user_id == uuid.UUID(user_id),
        OrganizationMember.organization_id == listing.seller_org_id
    ).first()
    return member is not None

def build_listing_response(listing: ScrapListing) -> dict:
    """Build response dict from listing object"""
    
    # Build media list
    media_list = []
    if hasattr(listing, 'media') and listing.media:
        for m in listing.media:
            media_list.append({
                "id": str(m.id),
                "file_url": m.file_url,
                "file_type": m.file_type,
                "is_primary": m.is_primary,
                "created_at": m.created_at.isoformat() if m.created_at else None
            })
    
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
        "view_count": listing.view_count,
        "created_at": listing.created_at.isoformat() if listing.created_at else None,
        "updated_at": listing.updated_at.isoformat() if listing.updated_at else None,
        "media": media_list
    }


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
    
    print(f"\n Creating listing for user: {current_user.email}")
    
    org_member = db.query(OrganizationMember).filter(
        OrganizationMember.user_id == current_user.id
    ).first()
    
    if not org_member:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User is not a member of any organization. Please create an organization first."
        )
    
    print(f"User is member of organization: {org_member.organization_id}")
    
    category = db.query(ScrapCategory).filter(
        ScrapCategory.id == uuid.UUID(listing_data.category_id)
    ).first()
    
    if not category:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid category ID"
        )
    
    print(f" Category found: {category.name}")
    
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
        
        print(f" Listing created with ID: {listing.id}")
        
        listing = db.query(ScrapListing).options(
            joinedload(ScrapListing.seller_org),
            joinedload(ScrapListing.category)
        ).filter(ScrapListing.id == listing.id).first()
        
        return build_listing_response(listing)
        
    except Exception as e:
        db.rollback()
        print(f" Error creating listing: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error creating listing: {str(e)}"
        )


@router.get("/", response_model=ListingListResponse)
async def get_listings(
    category_id: Optional[str] = Query(None, description="Filter by category ID"),
    material_name: Optional[str] = Query(None, description="Filter by material name (partial match)"),
    min_price: Optional[float] = Query(None, description="Minimum asking price"),
    max_price: Optional[float] = Query(None, description="Maximum asking price"),
    min_quantity: Optional[float] = Query(None, description="Minimum quantity"),
    max_quantity: Optional[float] = Query(None, description="Maximum quantity"),
    unit: Optional[ListingUnit] = Query(None, description="Unit (kg, tonne, unit, etc.)"),
    status: Optional[ListingStatus] = Query(ListingStatus.ACTIVE, description="Listing status"),

    city: Optional[str] = Query(None, description="Filter by city name"),
    state: Optional[str] = Query(None, description="Filter by state name"),
    # Location filter
    latitude: Optional[float] = Query(None, description="Latitude for location search"),
    longitude: Optional[float] = Query(None, description="Longitude for location search"),
    radius_km: Optional[float] = Query(10.0, description="Search radius in km"),
    
    page: int = Query(1, ge=1, description="Page number (starts at 1)"),
    size: int = Query(20, ge=1, le=100, description="Items per page (max 100)"),
    
    sort_by: str = Query("created_at", description="Sort field (created_at, asking_price, quantity)"),
    sort_order: str = Query("desc", description="Sort order (asc, desc)"),
    
    db: Session = Depends(get_db)
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
    
    print(f"\n Searching listings...")
    print(f"   Filters: category={category_id}, material={material_name}")
    print(f"   Page: {page}, Size: {size}")
    
    query = db.query(ScrapListing).options(
        joinedload(ScrapListing.seller_org),
        joinedload(ScrapListing.category),
        joinedload(ScrapListing.media)
    )
    
    if status:
        query = query.filter(ScrapListing.availability_status == status)
    else:
        query = query.filter(ScrapListing.availability_status == ListingStatus.ACTIVE)
    
    if category_id:
        try:
            query = query.filter(ScrapListing.category_id == uuid.UUID(category_id))
            print(f"   Filtering by category: {category_id}")
        except ValueError:
            print(f"   Invalid category ID: {category_id}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid category ID format"
            )
    
    if material_name:
        query = query.filter(ScrapListing.material_name.ilike(f"%{material_name}%"))
        print(f"   Filtering by material: {material_name}")
    
    if min_price is not None:
        query = query.filter(ScrapListing.asking_price >= min_price)
        print(f"   Filtering by min price: {min_price}")
    if max_price is not None:
        query = query.filter(ScrapListing.asking_price <= max_price)
        print(f"   Filtering by max price: {max_price}")
    
    if min_quantity is not None:
        query = query.filter(ScrapListing.quantity >= min_quantity)
    if max_quantity is not None:
        query = query.filter(ScrapListing.quantity <= max_quantity)
    
    if unit:
        query = query.filter(ScrapListing.unit == unit)
        print(f"   Filtering by unit: {unit}")
    
    if latitude and longitude:
        print(f"   Location filter: lat={latitude}, lon={longitude}, radius={radius_km}km")

    if city:
        query = query.filter(
            ScrapListing.location["city"].astext.ilike(f"%{city}%")
        )
        print(f"Filtering by city: {city}")
    
    if state:
        query = query.filter(
            ScrapListing.location["state"].astext.ilike(f"%{state}%")
        )
        print(f"Filtering by state: {state}")
    
    total = query.count()
    print(f"   Total matching listings: {total}")
    
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
    
    offset = (page - 1) * size
    query = query.offset(offset).limit(size)
    
    listings = query.all()
    print(f"   Retrieved {len(listings)} listings for page {page}")
    
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
    
    
    print(f"\n Fetching my listings for user: {current_user.email}")
    
    org_memberships = db.query(OrganizationMember).filter(
        OrganizationMember.user_id == current_user.id
    ).all()
    
    if not org_memberships:
        print(f"   User is not a member of any organization")
        return ListingListResponse(
            items=[],
            total=0,
            page=page,
            size=size,
            pages=0
        )
    
    org_ids = [m.organization_id for m in org_memberships]
    print(f"   User belongs to {len(org_ids)} organization(s)")
    
    query = db.query(ScrapListing).options(
        joinedload(ScrapListing.seller_org),
        joinedload(ScrapListing.category),
        joinedload(ScrapListing.media)
    ).filter(ScrapListing.seller_org_id.in_(org_ids))
    
    if status:
        query = query.filter(ScrapListing.availability_status == status)
        print(f"   Filtering by status: {status.value}")
    
    total = query.count()
    print(f"   Total listings: {total}")
    
    offset = (page - 1) * size
    listings = query.order_by(desc(ScrapListing.created_at)).offset(offset).limit(size).all()
    
    items = [build_listing_response(l) for l in listings]
    pages = (total + size - 1) // size if total > 0 else 0
    
    print(f"   Retrieved {len(listings)} listings for page {page}")
    
    return ListingListResponse(
        items=items,
        total=total,
        page=page,
        size=size,
        pages=pages
    )



@router.get("/map")
async def get_listings_for_map(
    category_id: Optional[str] = Query(None, description="Filter by category ID"),
    material_name: Optional[str] = Query(None, description="Filter by material name"),
    city: Optional[str] = Query(None, description="Filter by city"),
    state: Optional[str] = Query(None, description="Filter by state"),
    status: Optional[ListingStatus] = Query(ListingStatus.ACTIVE, description="Listing status"),
    limit: int = Query(500, ge=1, le=2000, description="Maximum markers to return"),
    db: Session = Depends(get_db)
):
    """
    Get listings with location data for Leaflet map display
    
    Features:
    - Public endpoint (no authentication required)
    - Returns only listings that have valid coordinates
    - Lightweight response optimized for map markers
    - Limits results to prevent performance issues
    
    Returns an array of markers with:
    - id, material_name, category, quantity, unit
    - asking_price, availability_status
    - latitude, longitude, city, state
    - primary_image_url (first image)
    """
    
    print(f"\n Fetching listings for map...")
    print(f"   Filters: category={category_id}, material={material_name}")
    print(f"   Limit: {limit}")
    
    query = db.query(ScrapListing).options(
        joinedload(ScrapListing.category),
        joinedload(ScrapListing.media),
        joinedload(ScrapListing.media)
    )

    
    if status:
        query = query.filter(ScrapListing.availability_status == status)
    else:
        query = query.filter(ScrapListing.availability_status == ListingStatus.ACTIVE)

    if city:
        query = query.filter(ScrapListing.location["city"].astext.ilike(f"%{city}%"))
    
    if state:
        query = query.filter(ScrapListing.location["state"].astext.ilike(f"%{state}%"))
    
    if category_id:
        try:
            query = query.filter(ScrapListing.category_id == uuid.UUID(category_id))
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid category ID format"
            )
    
    if material_name:
        query = query.filter(ScrapListing.material_name.ilike(f"%{material_name}%"))
    
    query = query.filter(ScrapListing.location.isnot(None))
    
    listings = query.limit(limit).all()
    
    print(f" Found {len(listings)} listings with locations")
    
    markers = []
    for listing in listings:
        location = listing.location or {}
        lat = location.get("latitude")
        lng = location.get("longitude")
        
        if lat is None or lng is None:
            continue
        
        primary_image = None
        if listing.media:
            for m in listing.media:
                if m.is_primary:
                    primary_image = m.file_url
                    break
            if not primary_image:
                primary_image = listing.media[0].file_url
        
        markers.append({
            "id": str(listing.id),
            "material_name": listing.material_name,
            "category_name": listing.category.name if listing.category else "Unknown",
            "quantity": str(listing.quantity),
            "unit": listing.unit.value,
            "asking_price": str(listing.asking_price) if listing.asking_price else None,
            "availability_status": listing.availability_status.value,
            "latitude": lat,
            "longitude": lng,
            "city": location.get("city"),
            "state": location.get("state"),
            "address": location.get("address"),
            "primary_image_url": primary_image
        })
    
    print(f"  Returning {len(markers)} markers with valid coordinates")
    
    return {
        "markers": markers,
        "total": len(markers)
    }


@router.get("/map/nearby")
async def get_nearby_listings(
    latitude: float = Query(..., description="Center latitude"),
    longitude: float = Query(..., description="Center longitude"),
    radius_km: float = Query(50.0, ge=1, le=500, description="Search radius in km"),
    category_id: Optional[str] = Query(None, description="Filter by category ID"),
    limit: int = Query(100, ge=1, le=500, description="Maximum results"),
    db: Session = Depends(get_db)
):
    """
    Get listings near a specific location
    
    Features:
    - Public endpoint
    - Uses Haversine formula for distance calculation
    - Returns listings sorted by distance (nearest first)
    - Requires latitude and longitude
    
    Note: For production use PostGIS for better performance.
    This implementation calculates distance in Python.
    """
    
    print(f"\n Finding nearby listings...")
    print(f"   Center: ({latitude}, {longitude}), Radius: {radius_km}km")
    
    query = db.query(ScrapListing).options(
        joinedload(ScrapListing.category),
        joinedload(ScrapListing.media)
    ).filter(
        ScrapListing.availability_status == ListingStatus.ACTIVE,
        ScrapListing.location.isnot(None)
    )
    
    if category_id:
        try:
            query = query.filter(ScrapListing.category_id == uuid.UUID(category_id))
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid category ID format"
            )
    
    listings = query.all()
    print(f"  Total listings to check: {len(listings)}")
    
    nearby = []
    for listing in listings:
        location = listing.location or {}
        lat = location.get("latitude")
        lng = location.get("longitude")
        
        if lat is None or lng is None:
            continue
        
        distance = haversine_distance(latitude, longitude, lat, lng)
        
        if distance <= radius_km:
            primary_image = None
            if listing.media:
                for m in listing.media:
                    if m.is_primary:
                        primary_image = m.file_url
                        break
                if not primary_image:
                    primary_image = listing.media[0].file_url
            
            nearby.append({
                "id": str(listing.id),
                "material_name": listing.material_name,
                "category_name": listing.category.name if listing.category else "Unknown",
                "quantity": str(listing.quantity),
                "unit": listing.unit.value,
                "asking_price": str(listing.asking_price) if listing.asking_price else None,
                "availability_status": listing.availability_status.value,
                "latitude": lat,
                "longitude": lng,
                "city": location.get("city"),
                "state": location.get("state"),
                "distance_km": round(distance, 2),
                "primary_image_url": primary_image
            })
    
    nearby.sort(key=lambda x: x["distance_km"])
    
    nearby = nearby[:limit]
    
    print(f" Found {len(nearby)} listings within {radius_km}km")
    
    return {
        "center": {"latitude": latitude, "longitude": longitude},
        "radius_km": radius_km,
        "listings": nearby,
        "total": len(nearby)
    }


# HAVERSINE DISTANCE HELPER

def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculate distance between two points on Earth using Haversine formula
    
    Returns distance in kilometers
    """
    R = 6371  
    
    lat1_rad = math.radians(lat1)
    lat2_rad = math.radians(lat2)
    delta_lat = math.radians(lat2 - lat1)
    delta_lon = math.radians(lon2 - lon1)
    
    a = (math.sin(delta_lat / 2) ** 2 +
         math.cos(lat1_rad) * math.cos(lat2_rad) *
         math.sin(delta_lon / 2) ** 2)
    
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    
    return R * c


@router.get("/{listing_id}", response_model=ListingResponse)
async def get_listing(
    listing_id: str,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user)
):
  
    
    print(f"\n Fetching listing: {listing_id}")
    
    listing = db.query(ScrapListing).options(
        joinedload(ScrapListing.seller_org),
        joinedload(ScrapListing.category)
    ).filter(ScrapListing.id == uuid.UUID(listing_id)).first()
    
    if not listing:
        print(f" Listing not found: {listing_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Listing not found"
        )
    
    print(f" Listing found: {listing.material_name}")

    is_owner = False
    if current_user:
        is_owner = check_listing_owner(listing, str(current_user.id), db)
    
    if not is_owner and listing.availability_status == ListingStatus.ACTIVE:
        listing.view_count += 1
        db.commit()
        db.refresh(listing)
        print(f"  View count incremented to {listing.view_count}")
    
    if listing.availability_status != ListingStatus.ACTIVE:
        print(f" Listing is {listing.availability_status.value}, checking access...")
        if not current_user:
            print(f" No user authenticated")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required to view this listing"
            )
        if not check_listing_owner(listing, str(current_user.id), db):
            print(f" User is not owner")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have access to this listing"
            )
        print(f" User is owner, access granted")
    
    return build_listing_response(listing)


@router.put("/{listing_id}", response_model=ListingResponse)
async def update_listing(
    listing_id: str,
    listing_data: ListingUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    
    
    print(f"\n Updating listing: {listing_id}")
    print(f"User: {current_user.email}")
    
    listing = db.query(ScrapListing).filter(
        ScrapListing.id == uuid.UUID(listing_id)
    ).first()
    
    if not listing:
        print(f" Listing not found: {listing_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Listing not found"
        )
    
    print(f" Listing found: {listing.material_name}")
    
    if not check_listing_owner(listing, str(current_user.id), db):
        print(f" User is not owner")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to update this listing"
        )
    
    print(f" User is owner, updating...")
    
    try:
        update_data = listing_data.dict(exclude_unset=True)
        print(f" Updating fields: {list(update_data.keys())}")
        
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
        
        for field, value in update_data.items():
            if value is not None:
                setattr(listing, field, value)
        
        db.commit()
        db.refresh(listing)
        print(f" Listing updated successfully")
        
        listing = db.query(ScrapListing).options(
            joinedload(ScrapListing.seller_org),
            joinedload(ScrapListing.category),
            joinedload(ScrapListing.media)
        ).filter(ScrapListing.id == listing.id).first()
        
        return build_listing_response(listing)
        
    except Exception as e:
        db.rollback()
        print(f" Error updating listing: {str(e)}")
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
   
    
    print(f"\n Deleting listing: {listing_id}")
    print(f"User: {current_user.email}")
    
    listing = db.query(ScrapListing).filter(
        ScrapListing.id == uuid.UUID(listing_id)
    ).first()
    
    if not listing:
        print(f" Listing not found: {listing_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Listing not found"
        )
    
    print(f" Listing found: {listing.material_name}")
    
    if not check_listing_owner(listing, str(current_user.id), db):
        print(f" User is not owner")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to delete this listing"
        )
    
    listing.availability_status = ListingStatus.CLOSED
    db.commit()
    
    print(f" Listing closed successfully")
    
    return None


@router.post("/{listing_id}/media", response_model=MediaUploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_listing_media(
    listing_id: str,
    file: UploadFile = File(...),
    is_primary: bool = Form(False),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Upload an image for a listing
    
    - Requires authentication
    - Only the listing owner can upload
    - Accepts image files (JPEG, PNG, WebP)
    - Max file size: 5MB
    """
    
    print(f"\n Uploading media for listing: {listing_id}")
    print(f"File: {file.filename}, Type: {file.content_type}")
    
    # 1. Get listing
    listing = db.query(ScrapListing).filter(
        ScrapListing.id == uuid.UUID(listing_id)
    ).first()
    
    if not listing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Listing not found"
        )
    
    # 2. Check ownership
    if not check_listing_owner(listing, str(current_user.id), db):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to upload media for this listing"
        )
    
    # 3. Validate file type
    allowed_types = ["image/jpeg", "image/jpg", "image/png", "image/webp"]
    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid file type. Allowed: {', '.join(allowed_types)}"
        )
    
    # 4. Validate file size (max 5MB)
    file_content = await file.read()
    if len(file_content) > 5 * 1024 * 1024:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File too large. Maximum size is 5MB"
        )
    
    # 5. Upload to Cloudinary
    upload_result = upload_image(file_content, folder="scraplink/listings")
    
    if not upload_result:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to upload image to Cloudinary"
        )
    
    print(f" Uploaded to Cloudinary: {upload_result['url']}")
    
    # 6. If this is primary, unset other primary images
    if is_primary:
        db.query(ListingMedia).filter(
            ListingMedia.listing_id == listing.id,
            ListingMedia.is_primary == True
        ).update({"is_primary": False})
    
    media = ListingMedia(
        id=uuid.uuid4(),
        listing_id=listing.id,
        uploaded_by=current_user.id,
        file_type=file.content_type,
        file_url=upload_result["url"],
        public_id=upload_result["public_id"],
        is_primary=is_primary
    )
    
    db.add(media)
    db.commit()
    db.refresh(media)
    
    print(f" Media record created: {media.id}")
    
    return MediaUploadResponse(
        message=" Image uploaded successfully",
        media=MediaResponse(
            id=str(media.id),
            listing_id=str(media.listing_id),
            file_type=media.file_type,
            file_url=media.file_url,
            public_id=media.public_id,
            is_primary=media.is_primary,
            created_at=media.created_at.isoformat() if media.created_at else None
        )
    )


@router.get("/{listing_id}/media", response_model=MediaListResponse)
async def get_listing_media(
    listing_id: str,
    db: Session = Depends(get_db)
):
    """
    Get all media for a listing
    
    - Public endpoint
    """
    
    listing = db.query(ScrapListing).filter(
        ScrapListing.id == uuid.UUID(listing_id)
    ).first()
    
    if not listing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Listing not found"
        )
    
    media_list = db.query(ListingMedia).filter(
        ListingMedia.listing_id == listing.id
    ).order_by(
        ListingMedia.is_primary.desc(),
        ListingMedia.created_at.asc()
    ).all()
    
    return MediaListResponse(
        media=[
            MediaResponse(
                id=str(m.id),
                listing_id=str(m.listing_id),
                file_type=m.file_type,
                file_url=m.file_url,
                public_id=m.public_id,
                is_primary=m.is_primary,
                created_at=m.created_at.isoformat() if m.created_at else None
            )
            for m in media_list
        ],
        total=len(media_list)
    )


@router.delete("/{listing_id}/media/{media_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_listing_media(
    listing_id: str,
    media_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Delete a media item from a listing
    
    - Requires authentication
    - Only the listing owner can delete
    """
    
    print(f"\n Deleting media: {media_id} from listing: {listing_id}")
    
    # 1. Get listing
    listing = db.query(ScrapListing).filter(
        ScrapListing.id == uuid.UUID(listing_id)
    ).first()
    
    if not listing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Listing not found"
        )
    
    if not check_listing_owner(listing, str(current_user.id), db):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to delete media from this listing"
        )
    
    media = db.query(ListingMedia).filter(
        ListingMedia.id == uuid.UUID(media_id),
        ListingMedia.listing_id == listing.id
    ).first()
    
    if not media:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Media not found"
        )
    
    if media.public_id:
        delete_image(media.public_id)
        print(f" Deleted from Cloudinary: {media.public_id}")
    
    db.delete(media)
    db.commit()
    
    print(f" Media record deleted")
    
    return None


@router.put("/{listing_id}/media/{media_id}/primary")
async def set_primary_media(
    listing_id: str,
    media_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Set a media item as the primary image for a listing
    """
    
    listing = db.query(ScrapListing).filter(
        ScrapListing.id == uuid.UUID(listing_id)
    ).first()
    
    if not listing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Listing not found"
        )
    
    if not check_listing_owner(listing, str(current_user.id), db):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to modify this listing"
        )
    
    media = db.query(ListingMedia).filter(
        ListingMedia.id == uuid.UUID(media_id),
        ListingMedia.listing_id == listing.id
    ).first()
    
    if not media:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Media not found"
        )
    
    db.query(ListingMedia).filter(
        ListingMedia.listing_id == listing.id
    ).update({"is_primary": False})
    
    media.is_primary = True
    db.commit()
    
    return {"message": "Primary image updated"}




@router.get("/stats/summary")
async def get_listing_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get listing statistics for the current user's organization
    
    - Requires authentication
    - Returns counts, total value, and category breakdown
    """
    from sqlalchemy import func
    
    print(f"\n Fetching stats for user: {current_user.email}")
    
    # Get user's organizations
    org_memberships = db.query(OrganizationMember).filter(
        OrganizationMember.user_id == current_user.id
    ).all()
    
    if not org_memberships:
        return {
            "total_listings": 0,
            "active_listings": 0,
            "sold_listings": 0,
            "closed_listings": 0,
            "total_value": "0.00",
            "by_category": []
        }
    
    org_ids = [m.organization_id for m in org_memberships]
    
    all_listings = db.query(ScrapListing).filter(
        ScrapListing.seller_org_id.in_(org_ids)
    ).all()
    
    total_listings = len(all_listings)
    active_listings = sum(1 for l in all_listings if l.availability_status == ListingStatus.ACTIVE)
    sold_listings = sum(1 for l in all_listings if l.availability_status == ListingStatus.SOLD)
    closed_listings = sum(1 for l in all_listings if l.availability_status == ListingStatus.CLOSED)
    
    total_value = sum(
        float(l.asking_price) * float(l.quantity) if l.asking_price else 0
        for l in all_listings if l.availability_status == ListingStatus.ACTIVE
    )
    
    # Category breakdown
    category_stats = {}
    for listing in all_listings:
        if listing.category:
            cat_name = listing.category.name
            if cat_name not in category_stats:
                category_stats[cat_name] = 0
            category_stats[cat_name] += 1
    
    by_category = [
        {"category": name, "count": count}
        for name, count in sorted(category_stats.items(), key=lambda x: x[1], reverse=True)
    ]
    
    print(f"   Total: {total_listings}, Active: {active_listings}")
    
    return {
        "total_listings": total_listings,
        "active_listings": active_listings,
        "sold_listings": sold_listings,
        "closed_listings": closed_listings,
        "total_value": f"{total_value:.2f}",
        "by_category": by_category
    }