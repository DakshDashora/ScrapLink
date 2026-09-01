import enum
from sqlalchemy import Column, Integer, String, Enum, DateTime, sql
from app.database import Base

class UserRole(str, enum.Enum):
    BUYER = "Buyer"
    SELLER = "Seller"
    ADMIN = "Admin"

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String(100), nullable=False)
    email = Column(String(150), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    role = Column(Enum(UserRole), nullable=False, default=UserRole.BUYER)
    gstin = Column(String(15), nullable=True)  # Mandatory for Sellers
    created_at = Column(DateTime(timezone=True), server_default=sql.func.now())

    def __repr__(self):
        return f"<User(id={self.id}, email={self.email}, role={self.role})>"