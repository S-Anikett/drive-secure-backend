from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from . import crud, models, schemas
from ...db.db import get_db
from sqlalchemy import func
from datetime import datetime


router = APIRouter()


@router.post("/login")
async def login(
    user: schemas.UserCreate,
    authentication: schemas.OtpAuthenticationCreate,
    db: Session = Depends(get_db),
):
    if len(user.mobile_number) != 10:
        raise HTTPException(status_code=400, detail="invalid mobile number")
    existing_user = crud.get_user_by_mobile(db, mobile=user.mobile_number)
    already_exist = False
    if existing_user:
        if existing_user.status == "active":
            already_exist = True
        otp_authentication = crud.create_user_otp_authentications(
            db=db, user_id=existing_user.id, authentication=authentication
        )
        # todo sendotp
    else:
        user = crud.create_user(db=db, user=user)
        otp_authentication = crud.create_user_otp_authentications(
            db=db, user_id=user.id, authentication=authentication
        )
        # todo sendotp
    user_data = {
        "user_id": otp_authentication.user_id,
        "authentication_id": otp_authentication.id,
        "ip_address": otp_authentication.ip_address,
        "user_agent": otp_authentication.user_agent,
        "user_already_exists": already_exist,
        "otp_expires_at": otp_authentication.user_agent,
    }
    return user_data


@router.post("/verify_otp")
async def verify_otp(
    verify_otp: schemas.VerifyOtp,
    user_session: schemas.UserSessionCreate,
    db: Session = Depends(get_db),
):
    try:
        otp_authentication = crud.get_otp_authentication_by_id(
            db=db, authentication_id=verify_otp.authentication_id
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail="authentication_id is invalid")
    user = crud.get_user(db=db, id=otp_authentication.user_id)
    if otp_authentication.otp_expires_at <= datetime.now():
        raise HTTPException(status_code=400, detail="OTP Timeout")
    if verify_otp.otp_code == otp_authentication.otp_code:
        otp_authentication.is_validated = True
        user.status = "active"
        user.referred_by = verify_otp.referral_code
        user_session = crud.create_user_session(
            db=db, user_id=otp_authentication.user_id, user_session=user_session
        )
        db.commit()
        db.refresh(user_session)
        return user_session
    else:
        raise HTTPException(status_code=400, detail="Invalid Otp")


@router.get("/resend_otp")
async def resend_otp(authentication_id: str, db: Session = Depends(get_db)):
    try:
        otp_authentication = crud.get_otp_authentication_by_id(
            db=db, authentication_id=authentication_id
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail="authentication id is incorrect")
    # todo sendotp
    return JSONResponse(status_code=200, content={"detail": "OTP sent again."})


@router.get("/get_user_session")
def get_user_session(
    session_id: str, require_user_details: bool = False, db: Session = Depends(get_db)
):
    try:
        user_session = crud.get_session_by_id(db=db, id=session_id)
    except Exception as e:
        raise HTTPException(status_code=400, detail="session id is incorrect")
    if (
        user_session
        and user_session.session_expires_at <= datetime.now()
        and user_session.is_active == False
    ):
        if user_session.is_active:
            user_session.is_active = False
            db.commit()
        raise HTTPException(status_code=401, detail="Unauthorized")

    if user_session and user_session.logout_time is None:
        if require_user_details:
            user = crud.get_user(db=db, id=user_session.user_id)
            rank = crud.get_rank_by_id(db=db, id=user.id)
            referral_count = crud.get_referral_count_by_id(db=db, id=user.id)
            if referral_count:
                ref_count = referral_count.referral_count
            else:
                ref_count = 0
            return {
                "session": user_session,
                "user": user,
                "rank": rank,
                "referral_count": ref_count,
            }
        else:
            return user_session

    elif user_session:
        raise HTTPException(status_code=401, detail="Unauthorized")
    else:
        raise HTTPException(status_code=403, detail="Unauthenticated")


@router.post("/start_trip")
async def start_trip(
    trip: schemas.TripCreate, session: schemas.Session, db: Session = Depends(get_db)
):
    user_session = get_user_session(
        session_id=session.session_id, require_user_details=False, db=db
    )
    trip = crud.create_trip(db=db, user_id=user_session.user_id, trip=trip)
    return trip


@router.post("/end_trip")
async def end_trip(
    trip: schemas.EndTrip, session: schemas.Session, db: Session = Depends(get_db)
):
    user_session = get_user_session(
        session_id=session.session_id, require_user_details=False, db=db
    )
    current_trip = crud.get_trip_by_id(db=db, id=trip.id)
    current_trip.end_latitude = trip.latitude
    current_trip.end_longitude = trip.longitude
    current_trip.end_time = datetime.now()
    user = crud.get_user(db=db, id=user_session.user_id)
    total_score = user.average_score * user.total_trips
    if current_trip.number_of_frames != 0:
        user.average_score = (
            total_score + (current_trip.total_score / current_trip.number_of_frames)
        ) / (user.total_trips + 1)
    user.total_trips = user.total_trips + 1
    db.commit()
    db.refresh(current_trip)
    return current_trip


@router.post("/logout")
async def logout(session: schemas.Session, db: Session = Depends(get_db)):
    user_session = get_user_session(
        session_id=session.session_id, require_user_details=False, db=db
    )
    user_session.logout_time = datetime.now()
    user_session.is_active = False
    db.commit()
    db.refresh(user_session)
    return user_session


@router.post("/update_profile")
async def update_profile(
    session: schemas.Session,
    profile: schemas.UserProfile,
    db: Session = Depends(get_db),
):
    user_session = get_user_session(
        session_id=session.session_id, require_user_details=False, db=db
    )

    user = crud.update_user_profile(
        db=db, user_id=user_session.user_id, profile=profile
    )
    user_session = get_user_session(
        session_id=session.session_id, require_user_details=True, db=db
    )
    return user_session
