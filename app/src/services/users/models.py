from sqlalchemy import (
    Boolean,
    Column,
    ForeignKey,
    Integer,
    String,
    Date,
    DateTime,
    func,
    Float,
    text
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid
from datetime import datetime

from ...db.db import Base


class User(Base):
    __tablename__ = "users"

    id = Column(UUID, primary_key=True, index=True,unique=True,server_default=text("gen_random_uuid()"))
    name = Column(String(length=100), nullable=True)
    country_code = Column(String(length=100), nullable=True, default='+91')
    mobile_number = Column(String(length=100), nullable=False)
    email = Column(String(length=100), nullable=True)
    birth_date = Column(Date, nullable=True)
    country = Column(String(length=100), nullable=True)
    gender = Column(String(length=100), nullable=True)
    referral_code = Column(String(length=100),nullable=False,unique=True)
    referred_by = Column(String,nullable=True)
    status = Column(String(length=100), nullable=False)
    average_score=Column(Float,nullable=True)
    total_trips = Column(Integer,nullable=True)
    created_at = Column(DateTime, nullable=False, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    user_sessions = relationship("UserSession", back_populates="session_user")
    authentication_attempts = relationship(
        "OtpAuthentication", back_populates="recipient"
    )
    trips = relationship("Trip",back_populates="operator")


class UserSession(Base):
    __tablename__ = "user_sessions"

    id = Column(UUID, primary_key=True, index=True,unique=True,server_default=text("gen_random_uuid()"))
    user_id = Column(UUID, ForeignKey("users.id"), nullable=False, index=True)
    ip_address = Column(String(length=50), nullable=False)
    user_agent = Column(String(length=100), nullable=False)
    login_time = Column(DateTime, nullable=False)
    logout_time = Column(DateTime, nullable=True)
    session_expires_at = Column(DateTime, nullable=False)
    is_active = Column(Boolean,nullable=False)
    created_at = Column(DateTime, nullable=False, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    session_user = relationship("User", back_populates="user_sessions")


class OtpAuthentication(Base):
    __tablename__ = "otp_authentications"

    id = Column(UUID, primary_key=True, index=True,unique=True,server_default=text("gen_random_uuid()"))
    user_id = Column(UUID, ForeignKey("users.id"), nullable=False, index=True)
    ip_address = Column(String(length=50), nullable=False)
    user_agent = Column(String(length=100), nullable=False)
    login_attempt_time = Column(DateTime, nullable=False, default=func.now())
    otp_code = Column(String(length=6), nullable=False)
    otp_expires_at = Column(
        DateTime, default=func.now() + func.text("INTERVAL 5 MINUTE")
    )
    is_validated = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime, nullable=False, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    recipient = relationship("User", back_populates="authentication_attempts")
    
    
class Trip(Base):
    __tablename__="trips"
    
    id = Column(UUID, primary_key=True, index=True,unique=True,server_default=text("gen_random_uuid()"))
    user_id = Column(UUID, ForeignKey("users.id"), nullable=False, index=True)
    start_latitude = Column(String(length=100),nullable=True)
    start_longitude = Column(String(length=100),nullable=True)
    end_latitude = Column(String(length=100),nullable=True)
    end_longitude = Column(String(length=100),nullable=True)
    start_time= Column(DateTime,nullable=False)
    end_time= Column(DateTime,nullable=True)
    number_of_frames = Column(Integer,nullable=True,default=0)
    total_score = Column(Float,nullable=True,default=0)
    created_at = Column(DateTime, nullable=False, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    operator = relationship("User",back_populates="trips")


    
    

