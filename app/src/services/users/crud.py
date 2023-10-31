from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, any_
from . import models, schemas
from datetime import datetime
from sqlalchemy.orm import aliased
from sqlalchemy import func


def get_user_by_mobile(db: Session, mobile: str):
    return db.query(models.User).filter(models.User.mobile_number == mobile).first()


def get_user(db: Session, id: str):
    return db.query(models.User).filter(models.User.id == id).first()


def get_user_by_refferal_code(db: Session, referral_code: str):
    return (
        db.query(models.User).filter(models.User.refferal_code == referral_code).first()
    )


def create_user_otp_authentications(
    db: Session, user_id: str, authentication: schemas.OtpAuthenticationCreate
):
    otp_authentication = models.OtpAuthentication(
        user_id=user_id,
        ip_address=authentication.ip_address,
        user_agent=authentication.user_agent,
        login_attempt_time=authentication.login_attempt_time,
        otp_code=authentication.otp_code,
        otp_expires_at=authentication.otp_expires_at,
    )
    db.add(otp_authentication)
    db.commit()
    db.refresh(otp_authentication)
    return otp_authentication


def create_user(db: Session, user: schemas.UserCreate):
    user = models.User(
        mobile_number=user.mobile_number,
        referral_code=user.referral_code,
        referred_by=user.referred_by,
        average_score=user.average_score,
        total_trips=user.total_trips,
        status=user.status,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def get_otp_authentication_by_id(db: Session, authentication_id: str):
    return (
        db.query(models.OtpAuthentication)
        .filter(models.OtpAuthentication.id == authentication_id)
        .first()
    )


def create_user_session(
    db: Session, user_id: str, user_session: schemas.UserSessionCreate
):
    user_session = models.UserSession(
        user_id=user_id,
        ip_address=user_session.ip_address,
        user_agent=user_session.user_agent,
        login_time=user_session.login_time,
        session_expires_at=user_session.session_expires_at,
        is_active=user_session.is_active,
    )
    db.add(user_session)
    db.commit()
    db.refresh(user_session)
    return user_session


def get_session_by_id(db: Session, id: str):
    return db.query(models.UserSession).filter(models.UserSession.id == id).first()


def get_rank_by_id(db: Session, id: str):
    rank_subquery = db.query(
        models.User.id.label("user_id"),
        func.rank().over(order_by=models.User.average_score.desc()).label("rank"),
    ).subquery()

    return db.query(rank_subquery.c.rank).filter(rank_subquery.c.user_id == id).scalar()


def get_referral_count_by_id(db: Session, id: str):
    user_alias = aliased(models.User, name="user_alias")
    return (
        db.query(func.count().label("referral_count"))
        .select_from(models.User)
        .join(user_alias, models.User.referral_code == user_alias.referred_by)
        .filter(models.User.id == id)
        .group_by(models.User.id)
        .first()
    )


def get_trip_by_id(db: Session, id: str):
    return db.query(models.Trip).filter(models.Trip.id == id).first()


def create_trip(db: Session, user_id: str, trip: schemas.TripCreate):
    trip = models.Trip(
        user_id=user_id,
        start_latitude=trip.latitude,
        start_longitude=trip.longitude,
        start_time=trip.start_time,
    )
    db.add(trip)
    db.commit()
    db.refresh(trip)
    return trip


def update_trip_frames_and_score(
    id: str,
    frame_score: float,
    db: Session,
):
    trip = get_trip_by_id(db=db, id=id)
    trip.number_of_frames = trip.number_of_frames + 1
    trip.total_score = trip.total_score + frame_score
    db.commit()
    return True


def update_user_profile(db: Session, user_id: str, profile: schemas.UserProfile):
    user = get_user(db=db, id=user_id)
    user.name = profile.name if profile.name is not None else user.name
    user.country_code = (
        profile.country_code if profile.country_code is not None else user.country_code
    )
    user.email = profile.email if profile.email is not None else user.email
    user.birth_date = (
        profile.birth_date if profile.birth_date is not None else user.birth_date
    )
    user.country = profile.country if profile.country is not None else user.country
    user.gender = profile.gender if profile.gender is not None else user.gender

    db.commit()
    db.refresh(user)
    return user
