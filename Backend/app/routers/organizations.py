from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User
from app.models.organization import Organization, VerificationStatus
from app.models.organization_member import OrganizationMember, MemberRole
from app.security import get_current_user
from app.schemas.organization import (
    OrganizationCreate, OrganizationUpdate, OrganizationResponse
)
import uuid

router = APIRouter(prefix="/organizations", tags=["Organizations"])


@router.post("/", response_model=OrganizationResponse, status_code=status.HTTP_201_CREATED)
async def create_organization(
    org_data: OrganizationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    existing = db.query(Organization).filter(
        Organization.name == org_data.name
    ).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Organization with this name already exists"
        )
    
    organization = Organization(
        id=uuid.uuid4(),
        name=org_data.name,
        business_type=org_data.business_type,
        industry_type=org_data.industry_type,
        description=org_data.description,
        location=org_data.location,
        gstin=org_data.gstin,
        owner_user_id=current_user.id,
        gstin_status=VerificationStatus.PENDING if org_data.gstin else VerificationStatus.NOT_APPLICABLE
    )
    
    db.add(organization)
    db.flush()  
    
    member = OrganizationMember(
        id=uuid.uuid4(),
        organization_id=organization.id,
        user_id=current_user.id,
        role=MemberRole.OWNER
    )
    db.add(member)
    
    db.commit()
    db.refresh(organization)
    
    return OrganizationResponse(
        id=str(organization.id),
        name=organization.name,
        business_type=organization.business_type,
        industry_type=organization.industry_type,
        description=organization.description,
        location=organization.location,
        gstin=organization.gstin,
        gstin_status=organization.gstin_status,
        verification_status=organization.verification_status,
        owner_user_id=str(organization.owner_user_id),
        created_at=organization.created_at.isoformat() if organization.created_at else None,
        updated_at=organization.updated_at.isoformat() if organization.updated_at else None
    )


@router.get("/{org_id}", response_model=OrganizationResponse)
async def get_organization(
    org_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get organization details"""
    organization = db.query(Organization).filter(
        Organization.id == uuid.UUID(org_id)
    ).first()
    
    if not organization:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found"
        )
    
    return OrganizationResponse(
        id=str(organization.id),
        name=organization.name,
        business_type=organization.business_type,
        industry_type=organization.industry_type,
        description=organization.description,
        location=organization.location,
        gstin=organization.gstin,
        gstin_status=organization.gstin_status,
        verification_status=organization.verification_status,
        owner_user_id=str(organization.owner_user_id),
        created_at=organization.created_at.isoformat() if organization.created_at else None,
        updated_at=organization.updated_at.isoformat() if organization.updated_at else None
    )


@router.put("/{org_id}", response_model=OrganizationResponse)
async def update_organization(
    org_id: str,
    org_data: OrganizationUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update organization details"""
    organization = db.query(Organization).filter(
        Organization.id == uuid.UUID(org_id)
    ).first()
    
    if not organization:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found"
        )
    
    if organization.owner_user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only organization owner can update details"
        )
    
    for field, value in org_data.dict(exclude_unset=True).items():
        if value is not None:
            setattr(organization, field, value)
    
    if org_data.gstin is not None:
        organization.gstin_status = (
            VerificationStatus.PENDING if org_data.gstin 
            else VerificationStatus.NOT_APPLICABLE
        )
    
    db.commit()
    db.refresh(organization)
    
    return OrganizationResponse(
        id=str(organization.id),
        name=organization.name,
        business_type=organization.business_type,
        industry_type=organization.industry_type,
        description=organization.description,
        location=organization.location,
        gstin=organization.gstin,
        gstin_status=organization.gstin_status,
        verification_status=organization.verification_status,
        owner_user_id=str(organization.owner_user_id),
        created_at=organization.created_at.isoformat() if organization.created_at else None,
        updated_at=organization.updated_at.isoformat() if organization.updated_at else None
    )