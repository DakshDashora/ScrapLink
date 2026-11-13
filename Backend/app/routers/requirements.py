from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import desc
from typing import Optional
import uuid
from decimal import Decimal

from app.database import get_db
from app.models.user import User
from app.models.buyer_requirement import BuyerRequirement, RequirementStatus, RequirementUnit
from app.models.organization_member import OrganizationMember
from app.models.scrap_category import ScrapCategory
from app.models.organization import Organization
from app.security import get_current_user
from app.schemas.buyer_requirement import (
    RequirementCreate, RequirementUpdate, RequirementResponse, RequirementListResponse
)

router = APIRouter(prefix="/api/requirements", tags=["Buyer Requirements"])


def get_user_org_id(user_id: str, db: Session) -> uuid.UUID:
    """Get the organization ID for the current user"""
    member = db.query(OrganizationMember).filter(
        OrganizationMember.user_id == uuid.UUID(user_id)
    ).first()
    if not member:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User is not a member of any organization"
        )
    return member.organization_id

def check_requirement_owner(req: BuyerRequirement, user_id: str, db: Session) -> bool:
    """Check if user belongs to the organization that owns the requirement"""
    member = db.query(OrganizationMember).filter(
        OrganizationMember.user_id == uuid.UUID(user_id),
        OrganizationMember.organization_id == req.buyer_org_id
    ).first()
    return member is not None

def build_requirement_response(req: BuyerRequirement) -> dict:
    """Build response dict"""
    return {
        "id": str(req.id),
        "buyer_org_id": str(req.buyer_org_id),
        "buyer_org_name": req.buyer_org.name if req.buyer_org else "Unknown",
        "category_id": str(req.category_id),
        "category_name": req.category.name if req.category else "Unknown",
        "material_name": req.material_name,
        "grade": req.grade,
        "description": req.description,
        "quantity": str(req.quantity),
        "unit": req.unit,
        "target_price": str(req.target_price) if req.target_price else None,
        "location": req.location,
        "status": req.status,
        "created_at": req.created_at.isoformat() if req.created_at else None,
        "updated_at": req.updated_at.isoformat() if req.updated_at else None,
    }



@router.post("/", response_model=RequirementResponse, status_code=status.HTTP_201_CREATED)
async def create_requirement(
    req_data: RequirementCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new buyer requirement"""
    print(f"\n Creating requirement for user: {current_user.email}")
    
    org_id = get_user_org_id(str(current_user.id), db)
    
    category = db.query(ScrapCategory).filter(
        ScrapCategory.id == uuid.UUID(req_data.category_id)
    ).first()
    if not category:
        raise HTTPException(status_code=400, detail="Invalid category ID")
    
    try:
        req = BuyerRequirement(
            id=uuid.uuid4(),
            buyer_org_id=org_id,
            category_id=uuid.UUID(req_data.category_id),
            material_name=req_data.material_name,
            grade=req_data.grade,
            description=req_data.description,
            quantity=req_data.quantity,
            unit=req_data.unit,
            target_price=req_data.target_price,
            location=req_data.location,
            status=RequirementStatus.OPEN
        )
        db.add(req)
        db.commit()
        db.refresh(req)
        
        req = db.query(BuyerRequirement).options(
            joinedload(BuyerRequirement.buyer_org),
            joinedload(BuyerRequirement.category)
        ).filter(BuyerRequirement.id == req.id).first()
        
        print(f" Requirement created: {req.id}")
        return build_requirement_response(req)
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"Error: {str(e)}")


@router.get("/", response_model=RequirementListResponse)
async def get_my_requirements(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    status: Optional[RequirementStatus] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get requirements for the current user's organization"""
    org_id = get_user_org_id(str(current_user.id), db)
    
    query = db.query(BuyerRequirement).options(
        joinedload(BuyerRequirement.buyer_org),
        joinedload(BuyerRequirement.category)
    ).filter(BuyerRequirement.buyer_org_id == org_id)
    
    if status:
        query = query.filter(BuyerRequirement.status == status)
        
    total = query.count()
    offset = (page - 1) * size
    reqs = query.order_by(desc(BuyerRequirement.created_at)).offset(offset).limit(size).all()
    
    items = [build_requirement_response(r) for r in reqs]
    pages = (total + size - 1) // size if total > 0 else 0
    
    return RequirementListResponse(
        items=items, total=total, page=page, size=size, pages=pages
    )


@router.get("/{requirement_id}", response_model=RequirementResponse)
async def get_requirement(
    requirement_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a single requirement by ID (owner only)"""
    req = db.query(BuyerRequirement).options(
        joinedload(BuyerRequirement.buyer_org),
        joinedload(BuyerRequirement.category)
    ).filter(BuyerRequirement.id == uuid.UUID(requirement_id)).first()
    
    if not req:
        raise HTTPException(status_code=404, detail="Requirement not found")
        
    if not check_requirement_owner(req, str(current_user.id), db):
        raise HTTPException(status_code=403, detail="Not authorized to view this requirement")
        
    return build_requirement_response(req)


@router.put("/{requirement_id}", response_model=RequirementResponse)
async def update_requirement(
    requirement_id: str,
    req_data: RequirementUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update a requirement (owner only)"""
    req = db.query(BuyerRequirement).filter(
        BuyerRequirement.id == uuid.UUID(requirement_id)
    ).first()
    
    if not req:
        raise HTTPException(status_code=404, detail="Requirement not found")
        
    if not check_requirement_owner(req, str(current_user.id), db):
        raise HTTPException(status_code=403, detail="Not authorized to edit this requirement")
        
    try:
        update_data = req_data.dict(exclude_unset=True)
        
        if "category_id" in update_data and update_data["category_id"]:
            cat = db.query(ScrapCategory).filter(ScrapCategory.id == uuid.UUID(update_data["category_id"])).first()
            if not cat:
                raise HTTPException(status_code=400, detail="Invalid category ID")
            req.category_id = uuid.UUID(update_data["category_id"])
            del update_data["category_id"]
            
        for field, value in update_data.items():
            if value is not None:
                setattr(req, field, value)
                
        db.commit()
        db.refresh(req)
        
        req = db.query(BuyerRequirement).options(
            joinedload(BuyerRequirement.buyer_org),
            joinedload(BuyerRequirement.category)
        ).filter(BuyerRequirement.id == req.id).first()
        
        return build_requirement_response(req)
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"Error updating: {str(e)}")


@router.delete("/{requirement_id}", status_code=status.HTTP_204_NO_CONTENT)
async def deactivate_requirement(
    requirement_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Deactivate a requirement (owner only)"""
    req = db.query(BuyerRequirement).filter(
        BuyerRequirement.id == uuid.UUID(requirement_id)
    ).first()
    
    if not req:
        raise HTTPException(status_code=404, detail="Requirement not found")
        
    if not check_requirement_owner(req, str(current_user.id), db):
        raise HTTPException(status_code=403, detail="Not authorized to delete this requirement")
        
    req.status = RequirementStatus.CLOSED
    db.commit()
    return None