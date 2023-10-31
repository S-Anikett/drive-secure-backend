from pydantic import BaseModel, validator
from datetime import datetime, timedelta
from datetime import date
import random
import string, secrets


class UserBase(BaseModel):
    mobile_number: str


class UserCreate(UserBase):
    status: str = "inactive"
    referral_code: str = None
    referred_by: str = None
    average_score: float = 0
    total_trips: int = 0

    @validator("referral_code", pre=True, always=True)
    def generate_refferal_code(cls, v):
        if v:
            return v
        length = 10
        characters = string.ascii_letters + string.digits
        referral_code = "".join(secrets.choice(characters) for _ in range(length))
        return referral_code

    # class Config:
    #     orm_mode=True


class User(UserBase):
    id: str
    name: str
    country_code: str
    email: str
    birth_date: date
    country: str
    gender: str
    status: str

    class Config:
        orm_mode = True


class OtpAuthenticationBase(BaseModel):
    ip_address: str
    user_agent: str


class OtpAuthenticationCreate(OtpAuthenticationBase):
    login_attempt_time: datetime = None
    otp_code: str = None
    otp_expires_at: datetime = None

    @validator("login_attempt_time", pre=True, always=True)
    def set_login_attempt_time(cls, v):
        if v:
            return v
        return datetime.now()

    @validator("otp_code", pre=True, always=True)
    def generate_otp_code(cls, v):
        if v:
            return v
        # return str(random.randint(100000, 999999))
        return 967673

    @validator("otp_expires_at", pre=True, always=True)
    def set_otp_expires_at(cls, v):
        if v:
            return v
        return datetime.now() + timedelta(minutes=5)

    class Config:
        orm_mode = True


class VerifyOtp(BaseModel):
    otp_code: str
    authentication_id: str
    referral_code: str = None

    class Config:
        orm_mode = True


class UserSessionBase(BaseModel):
    ip_address: str
    user_agent: str


class UserSessionCreate(UserSessionBase):
    login_time: datetime = None
    session_expires_at: datetime = None
    is_active: bool = True

    @validator("login_time", pre=True, always=True)
    def set_login_time(cls, v):
        if v:
            return v
        return datetime.now()

    @validator("session_expires_at", pre=True, always=True)
    def set_session_expires_at(cls, v):
        if v:
            return v
        return datetime.now() + timedelta(days=365)

    class Config:
        orm_mode = True


class TripBase(BaseModel):
    latitude: str
    longitude: str


class TripCreate(TripBase):
    start_time: datetime = None

    @validator("start_time", pre=True, always=True)
    def set_trip_start_time(cls, v):
        if v:
            return v
        return datetime.now()

    class Config:
        orm_mode = True


class EndTrip(BaseModel):
    id: str
    latitude: str
    longitude: str


class Session(BaseModel):
    session_id: str


class drowsiness(BaseModel):
    image: str = ""
    trip_id: str = ""


class UserProfile(BaseModel):
    name: str = None
    country_code: str = "+91"
    email: str = None
    birth_date: date = None
    country: str = None
    gender: str = None
