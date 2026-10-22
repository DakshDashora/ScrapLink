from sqlalchemy import Column, String, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from pgvector.sqlalchemy import Vector
from app.database import Base
import uuid


class RequirementEmbedding(Base):
    __tablename__ = "requirement_embeddings"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    requirement_id = Column(
        UUID(as_uuid=True), 
        ForeignKey("buyer_requirements.id", ondelete="CASCADE"), 
        nullable=False, 
        index=True
    )
    
    embedding = Column(Vector(384), nullable=False)
    
    model_name = Column(String, nullable=False, default="all-MiniLM-L6-v2")
    model_version = Column(String, nullable=False, default="v1")
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    requirement = relationship("BuyerRequirement", backref="embeddings")

    def __repr__(self):
        return f"<RequirementEmbedding req={self.requirement_id}>"