from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import desc
from typing import Optional
import uuid

from app.database import get_db
from app.models.user import User
from app.models.scrap_listing import ScrapListing, ListingStatus
from app.models.organization_member import OrganizationMember
from app.models.scrap_category import ScrapCategory
from app.models.organization import Organization
from app.security import get_current_user
from app.schemas.scrap_listing import (
    ListingCreate, ListingUpdate, ListingResponse
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
# API ENDPOINTS - DAY 1
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