from sqlalchemy import Column, String, Text, DateTime, ForeignKey, Numeric, Enum, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base
import uuid
from enum import Enum as PyEnum


class RequirementStatus(str, PyEnum):
    OPEN = "Open"
    MATCHED = "Matched"
    CLOSED = "Closed"


class RequirementUnit(str, PyEnum):
    KG = "kg"
    TONNE = "tonne"
    UNIT = "unit"
    METER = "meter"
    LITER = "liter"


class BuyerRequirement(Base):
    __tablename__ = "buyer_requirements"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    buyer_org_id = Column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id"),
        nullable=False,
        index=True
    )
    category_id = Column(
        UUID(as_uuid=True),
        ForeignKey("scrap_categories.id"),
        nullable=False,
        index=True
    )

    material_name = Column(String, nullable=False)
    grade = Column(String, nullable=True)
    description = Column(Text, nullable=True)

    quantity = Column(Numeric(10, 2), nullable=False)
    unit = Column(Enum(RequirementUnit), nullable=False, default=RequirementUnit.KG)
    target_price = Column(Numeric(10, 2), nullable=True)

    location = Column(JSON, nullable=True)

    status = Column(
        Enum(RequirementStatus),
        nullable=False,
        default=RequirementStatus.OPEN,
        index=True
    )

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    buyer_org = relationship("Organization", foreign_keys=[buyer_org_id])
    category = relationship("ScrapCategory")

    def __repr__(self):
        return f"<BuyerRequirement {self.material_name} by org {self.buyer_org_id}>"