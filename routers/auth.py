import secrets
from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends, HTTPException, status, Response, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_
from database import get_database_session
from config import settings
from models import UserAccount, EmailVerificationRecord
from schemas import (
    UserRegistrationRequest,
    UserAccountResponse,
    AuthenticationTokenResponse,
    RefreshTokenRequest,
    EmailVerificationRequest,
    ResendOtpRequest,
    ForgotPasswordRequest,
    ResetPasswordRequest,
    GenericMessageResponse
)
from security import (
    hash_user_password,
    verify_user_password,
    create_signed_access_token,
    create_signed_refresh_token,
    decode_and_verify_token,
    get_authenticated_user
)
from services.email_service import EmailNotificationService

router = APIRouter(prefix="/api/auth", tags=["Authentication"])

def generate_secure_otp() -> str:
    return str(secrets.randbelow(900000) + 100000)

@router.post("/register", response_model=GenericMessageResponse, status_code=status.HTTP_201_CREATED)
async def register_new_user_account(
    registration_data: UserRegistrationRequest,
    database_session: AsyncSession = Depends(get_database_session)
):
    clean_username = registration_data.username.strip()
    clean_email = registration_data.email_address.strip().lower()

    verification_query = select(UserAccount).where(
        or_(
            UserAccount.email_address.ilike(clean_email),
            UserAccount.username.ilike(clean_username)
        )
    )
    existing_result = await database_session.execute(verification_query)
    existing_user = existing_result.scalar_one_or_none()

    if existing_user:
        if existing_user.is_verified:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username or email address is already in use"
            )
        target_user = existing_user
        target_user.username = clean_username
        target_user.hashed_password = hash_user_password(registration_data.password)
    else:
        target_user = UserAccount(
            email_address=clean_email,
            username=clean_username,
            hashed_password=hash_user_password(registration_data.password),
            is_verified=False
        )
        database_session.add(target_user)

    otp_code = generate_secure_otp()
    expiration_time = datetime.now(timezone.utc) + timedelta(minutes=settings.otp_expiration_minutes)

    verification_record = EmailVerificationRecord(
        email_address=clean_email,
        otp_code=otp_code,
        purpose="registration",
        expires_at=expiration_time,
        is_used=False
    )
    database_session.add(verification_record)
    await database_session.commit()

    email_sent = EmailNotificationService.send_verification_email(
        recipient_email=clean_email,
        recipient_username=clean_username,
        otp_code=otp_code,
        action_title="Account Email Verification"
    )

    detail_message = f"Registration initiated. Verification OTP sent to {clean_email}"
    if not email_sent:
        detail_message = f"Account registered. (Sandbox OTP: {otp_code})"

    return GenericMessageResponse(message=detail_message)

@router.post("/verify-email", response_model=AuthenticationTokenResponse)
async def verify_email_address(
    payload: EmailVerificationRequest,
    response: Response,
    database_session: AsyncSession = Depends(get_database_session)
):
    clean_email = payload.email_address.strip().lower()
    otp_query = (
        select(EmailVerificationRecord)
        .where(
            EmailVerificationRecord.email_address.ilike(clean_email),
            EmailVerificationRecord.otp_code == payload.otp_code.strip(),
            EmailVerificationRecord.purpose == "registration",
            EmailVerificationRecord.is_used == False
        )
        .order_by(EmailVerificationRecord.created_at.desc())
    )
    otp_result = await database_session.execute(otp_query)
    record = otp_result.scalar_one_or_none()

    if not record:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid verification code or code already used"
        )

    current_utc = datetime.now(timezone.utc)
    record_expires = record.expires_at
    if record_expires.tzinfo is None:
        record_expires = record_expires.replace(tzinfo=timezone.utc)

    if record_expires < current_utc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Verification code has expired. Please request a new one"
        )

    record.is_used = True

    user_query = select(UserAccount).where(UserAccount.email_address.ilike(clean_email))
    user_result = await database_session.execute(user_query)
    user = user_result.scalar_one_or_none()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User account not found"
        )

    user.is_verified = True
    await database_session.commit()

    access_token_string = create_signed_access_token(user_identifier=user.username)
    refresh_token_string = create_signed_refresh_token(user_identifier=user.username)

    response.set_cookie(
        key="access_token",
        value=access_token_string,
        httponly=True,
        samesite="lax",
        secure=False,
        max_age=settings.access_token_expire_minutes * 60,
        path="/"
    )

    return {
        "access_token": access_token_string,
        "refresh_token": refresh_token_string,
        "token_type": "bearer"
    }

@router.post("/resend-otp", response_model=GenericMessageResponse)
async def resend_verification_otp(
    payload: ResendOtpRequest,
    database_session: AsyncSession = Depends(get_database_session)
):
    clean_email = payload.email_address.strip().lower()
    user_query = select(UserAccount).where(UserAccount.email_address.ilike(clean_email))
    user_result = await database_session.execute(user_query)
    user = user_result.scalar_one_or_none()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No account associated with this email"
        )

    if user.is_verified:
        return GenericMessageResponse(message="Account is already verified. You can log in directly")

    otp_code = generate_secure_otp()
    expiration_time = datetime.now(timezone.utc) + timedelta(minutes=settings.otp_expiration_minutes)

    verification_record = EmailVerificationRecord(
        email_address=clean_email,
        otp_code=otp_code,
        purpose="registration",
        expires_at=expiration_time,
        is_used=False
    )
    database_session.add(verification_record)
    await database_session.commit()

    email_sent = EmailNotificationService.send_verification_email(
        recipient_email=clean_email,
        recipient_username=user.username,
        otp_code=otp_code,
        action_title="New Verification Code"
    )

    detail_message = f"Fresh verification code sent to {clean_email}"
    if not email_sent:
        detail_message = f"Fresh code generated. (Sandbox OTP: {otp_code})"

    return GenericMessageResponse(message=detail_message)

@router.post("/login", response_model=AuthenticationTokenResponse)
async def login_and_generate_token(
    request: Request,
    response: Response,
    database_session: AsyncSession = Depends(get_database_session)
):
    header_content_type = request.headers.get("content-type", "").lower()
    if "application/json" in header_content_type:
        json_data = await request.json()
        input_username = str(json_data.get("username", "")).strip()
        input_password = str(json_data.get("password", "")).strip()
    else:
        form_data = await request.form()
        input_username = str(form_data.get("username", "")).strip()
        input_password = str(form_data.get("password", "")).strip()

    if not input_username or not input_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username and password are required"
        )

    account_lookup_query = select(UserAccount).where(
        or_(
            UserAccount.username.ilike(input_username),
            UserAccount.email_address.ilike(input_username)
        )
    )
    query_result = await database_session.execute(account_lookup_query)
    user_account = query_result.scalar_one_or_none()

    if not user_account or not verify_user_password(input_password, user_account.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user_account.is_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account email is not verified. Please verify your email with the OTP sent to your inbox"
        )

    access_token_string = create_signed_access_token(user_identifier=user_account.username)
    refresh_token_string = create_signed_refresh_token(user_identifier=user_account.username)

    response.set_cookie(
        key="access_token",
        value=access_token_string,
        httponly=True,
        samesite="lax",
        secure=False,
        max_age=settings.access_token_expire_minutes * 60,
        path="/"
    )

    return {
        "access_token": access_token_string,
        "refresh_token": refresh_token_string,
        "token_type": "bearer"
    }

@router.post("/refresh", response_model=AuthenticationTokenResponse)
async def refresh_access_token(
    payload: RefreshTokenRequest,
    response: Response,
    database_session: AsyncSession = Depends(get_database_session)
):
    token_payload = decode_and_verify_token(payload.refresh_token, expected_type="refresh")
    if not token_payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token"
        )

    username = token_payload.get("sub")
    query = select(UserAccount).where(UserAccount.username == username)
    result = await database_session.execute(query)
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User associated with token no longer exists"
        )

    new_access_token = create_signed_access_token(user_identifier=user.username)
    new_refresh_token = create_signed_refresh_token(user_identifier=user.username)

    response.set_cookie(
        key="access_token",
        value=new_access_token,
        httponly=True,
        samesite="lax",
        secure=False,
        max_age=settings.access_token_expire_minutes * 60,
        path="/"
    )

    return {
        "access_token": new_access_token,
        "refresh_token": new_refresh_token,
        "token_type": "bearer"
    }

@router.post("/logout", response_model=GenericMessageResponse)
async def logout_user_session(response: Response):
    response.delete_cookie(key="access_token", path="/")
    return GenericMessageResponse(message="Successfully logged out")

@router.post("/forgot-password", response_model=GenericMessageResponse)
async def forgot_password_request(
    payload: ForgotPasswordRequest,
    database_session: AsyncSession = Depends(get_database_session)
):
    clean_email = payload.email_address.strip().lower()
    query = select(UserAccount).where(UserAccount.email_address.ilike(clean_email))
    result = await database_session.execute(query)
    user = result.scalar_one_or_none()

    if not user:
        return GenericMessageResponse(message="If the email exists, a reset code has been sent")

    otp_code = generate_secure_otp()
    expiration_time = datetime.now(timezone.utc) + timedelta(minutes=settings.otp_expiration_minutes)

    verification_record = EmailVerificationRecord(
        email_address=clean_email,
        otp_code=otp_code,
        purpose="password_reset",
        expires_at=expiration_time,
        is_used=False
    )
    database_session.add(verification_record)
    await database_session.commit()

    email_sent = EmailNotificationService.send_verification_email(
        recipient_email=clean_email,
        recipient_username=user.username,
        otp_code=otp_code,
        action_title="Password Reset Request"
    )

    detail_message = f"Password reset code sent to {clean_email}"
    if not email_sent:
        detail_message = f"Password reset code generated. (Sandbox OTP: {otp_code})"

    return GenericMessageResponse(message=detail_message)

@router.post("/reset-password", response_model=GenericMessageResponse)
async def reset_password_with_otp(
    payload: ResetPasswordRequest,
    database_session: AsyncSession = Depends(get_database_session)
):
    clean_email = payload.email_address.strip().lower()
    otp_query = (
        select(EmailVerificationRecord)
        .where(
            EmailVerificationRecord.email_address.ilike(clean_email),
            EmailVerificationRecord.otp_code == payload.otp_code.strip(),
            EmailVerificationRecord.purpose == "password_reset",
            EmailVerificationRecord.is_used == False
        )
        .order_by(EmailVerificationRecord.created_at.desc())
    )
    otp_result = await database_session.execute(otp_query)
    record = otp_result.scalar_one_or_none()

    if not record:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid reset code or code already used"
        )

    current_utc = datetime.now(timezone.utc)
    record_expires = record.expires_at
    if record_expires.tzinfo is None:
        record_expires = record_expires.replace(tzinfo=timezone.utc)

    if record_expires < current_utc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Reset code has expired. Please request a new one"
        )

    record.is_used = True

    user_query = select(UserAccount).where(UserAccount.email_address.ilike(clean_email))
    user_result = await database_session.execute(user_query)
    user = user_result.scalar_one_or_none()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User account not found"
        )

    user.hashed_password = hash_user_password(payload.new_password)
    await database_session.commit()

    return GenericMessageResponse(message="Password reset successfully. You can now log in with your new password")

@router.get("/me", response_model=UserAccountResponse)
async def get_current_user_profile(
    current_authenticated_user: UserAccount = Depends(get_authenticated_user)
):
    return current_authenticated_user
