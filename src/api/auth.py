"""
Authentication API Endpoints

REST API for authentication operations.
"""

from typing import Optional
from fastapi import APIRouter, HTTPException, Request, Depends
from pydantic import BaseModel, EmailStr, Field

from ..auth import (
    AuthService,
    User,
    UserRole,
    get_current_user_required,
    get_current_user,
    RoleChecker,
)
from ..auth.service import get_auth_service


router = APIRouter(prefix="/api/v1/auth", tags=["Authentication"])


# Request/Response models
class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)
    name: str = Field(min_length=2)
    role: str = "doctor"
    specialty: Optional[str] = None
    institution: Optional[str] = None
    registration_number: Optional[str] = None


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "Bearer"
    expires_in: int
    user: dict


class RefreshRequest(BaseModel):
    refresh_token: str


class PasswordChangeRequest(BaseModel):
    current_password: str
    new_password: str = Field(min_length=8)


class PasswordResetRequest(BaseModel):
    email: EmailStr


class PasswordResetConfirm(BaseModel):
    token: str
    new_password: str = Field(min_length=8)


class ProfileUpdateRequest(BaseModel):
    name: Optional[str] = None
    specialty: Optional[str] = None
    institution: Optional[str] = None
    phone: Optional[str] = None


class SSOInitRequest(BaseModel):
    provider: str  # "google" or "microsoft"
    redirect_uri: str


class SSOCallbackRequest(BaseModel):
    state: str
    code: str


class UserResponse(BaseModel):
    id: str
    email: str
    name: str
    role: str
    specialty: Optional[str]
    institution: Optional[str]
    is_verified: bool
    email_verified: bool
    mfa_enabled: bool
    license_tier: str
    avatar_url: Optional[str]


# Endpoints
@router.post("/register", response_model=UserResponse)
async def register(request: RegisterRequest):
    """
    Register a new user with email/password.
    """
    auth = get_auth_service()

    try:
        role = UserRole(request.role)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid role: {request.role}")

    result = auth.register(
        email=request.email,
        password=request.password,
        name=request.name,
        role=role,
        specialty=request.specialty,
        institution=request.institution,
        registration_number=request.registration_number,
    )

    if not result.success:
        raise HTTPException(status_code=400, detail=result.error)

    return UserResponse(
        id=result.user.id,
        email=result.user.email,
        name=result.user.name,
        role=result.user.role.value,
        specialty=result.user.specialty,
        institution=result.user.institution,
        is_verified=result.user.is_verified,
        email_verified=result.user.email_verified,
        mfa_enabled=result.user.mfa_enabled,
        license_tier=result.user.license_tier,
        avatar_url=result.user.avatar_url,
    )


@router.post("/login", response_model=TokenResponse)
async def login(request: LoginRequest, req: Request):
    """
    Authenticate with email/password.
    """
    auth = get_auth_service()

    result = auth.login(
        email=request.email,
        password=request.password,
        ip_address=req.client.host if req.client else None,
        user_agent=req.headers.get("User-Agent"),
    )

    if not result.success:
        if result.requires_mfa:
            return {
                "requires_mfa": True,
                "mfa_token": result.mfa_token,
            }
        raise HTTPException(status_code=401, detail=result.error)

    return TokenResponse(
        access_token=result.tokens.access_token,
        refresh_token=result.tokens.refresh_token,
        token_type=result.tokens.token_type,
        expires_in=result.tokens.expires_in,
        user=result.user.to_dict(),
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_tokens(request: RefreshRequest):
    """
    Refresh access token using refresh token.
    """
    auth = get_auth_service()

    result = auth.refresh_tokens(request.refresh_token)

    if not result.success:
        raise HTTPException(status_code=401, detail=result.error)

    return TokenResponse(
        access_token=result.tokens.access_token,
        refresh_token=result.tokens.refresh_token,
        token_type=result.tokens.token_type,
        expires_in=result.tokens.expires_in,
        user=result.user.to_dict(),
    )


@router.post("/logout")
async def logout(request: RefreshRequest):
    """
    Logout and revoke session.
    """
    auth = get_auth_service()
    success = auth.logout(request.refresh_token)

    return {"success": success}


@router.post("/logout-all")
async def logout_all(
    user: User = Depends(get_current_user_required),
):
    """
    Logout from all sessions.
    """
    auth = get_auth_service()
    count = auth.logout_all(user.id)

    return {"success": True, "sessions_revoked": count}


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    user: User = Depends(get_current_user_required),
):
    """
    Get current user info.
    """
    return UserResponse(
        id=user.id,
        email=user.email,
        name=user.name,
        role=user.role.value,
        specialty=user.specialty,
        institution=user.institution,
        is_verified=user.is_verified,
        email_verified=user.email_verified,
        mfa_enabled=user.mfa_enabled,
        license_tier=user.license_tier,
        avatar_url=user.avatar_url,
    )


@router.patch("/me", response_model=UserResponse)
async def update_profile(
    request: ProfileUpdateRequest,
    user: User = Depends(get_current_user_required),
):
    """
    Update current user profile.
    """
    auth = get_auth_service()

    result = auth.update_profile(
        user_id=user.id,
        name=request.name,
        specialty=request.specialty,
        institution=request.institution,
        phone=request.phone,
    )

    if not result.success:
        raise HTTPException(status_code=400, detail=result.error)

    return UserResponse(
        id=result.user.id,
        email=result.user.email,
        name=result.user.name,
        role=result.user.role.value,
        specialty=result.user.specialty,
        institution=result.user.institution,
        is_verified=result.user.is_verified,
        email_verified=result.user.email_verified,
        mfa_enabled=result.user.mfa_enabled,
        license_tier=result.user.license_tier,
        avatar_url=result.user.avatar_url,
    )


@router.post("/change-password")
async def change_password(
    request: PasswordChangeRequest,
    user: User = Depends(get_current_user_required),
):
    """
    Change password for current user.
    """
    auth = get_auth_service()

    result = auth.change_password(
        user_id=user.id,
        current_password=request.current_password,
        new_password=request.new_password,
    )

    if not result.success:
        raise HTTPException(status_code=400, detail=result.error)

    return {"success": True, "message": "Password changed. Please login again."}


@router.post("/forgot-password")
async def forgot_password(request: PasswordResetRequest):
    """
    Request password reset email.
    """
    auth = get_auth_service()

    # Always return success (don't reveal if email exists)
    token = auth.request_password_reset(request.email)

    # In production, send email instead of returning token
    return {
        "success": True,
        "message": "If the email exists, a reset link has been sent.",
        # Remove this in production:
        "_dev_token": token,
    }


@router.post("/reset-password")
async def reset_password(request: PasswordResetConfirm):
    """
    Reset password using token.
    """
    auth = get_auth_service()

    result = auth.reset_password(
        token=request.token,
        new_password=request.new_password,
    )

    if not result.success:
        raise HTTPException(status_code=400, detail=result.error)

    return {"success": True, "message": "Password reset successfully."}


@router.get("/sessions")
async def get_sessions(
    user: User = Depends(get_current_user_required),
):
    """
    Get all active sessions for current user.
    """
    auth = get_auth_service()
    sessions = auth.get_active_sessions(user.id)

    return {"sessions": sessions}


# SSO Endpoints
@router.post("/sso/init")
async def init_sso(request: SSOInitRequest):
    """
    Initialize SSO flow.

    Returns the authorization URL to redirect the user to.
    """
    auth = get_auth_service()

    result = auth.get_sso_url(request.provider, request.redirect_uri)

    if not result:
        raise HTTPException(
            status_code=400,
            detail=f"SSO provider '{request.provider}' not configured"
        )

    url, state = result
    return {"authorization_url": url, "state": state}


@router.post("/sso/callback", response_model=TokenResponse)
async def sso_callback(request: SSOCallbackRequest, req: Request):
    """
    Handle SSO callback.

    Exchange authorization code for tokens and create session.
    """
    auth = get_auth_service()

    result = await auth.handle_sso_callback(
        state=request.state,
        code=request.code,
        ip_address=req.client.host if req.client else None,
        user_agent=req.headers.get("User-Agent"),
    )

    if not result.success:
        raise HTTPException(status_code=401, detail=result.error)

    return TokenResponse(
        access_token=result.tokens.access_token,
        refresh_token=result.tokens.refresh_token,
        token_type=result.tokens.token_type,
        expires_in=result.tokens.expires_in,
        user=result.user.to_dict(),
    )


# Admin endpoints
@router.get("/users")
async def list_users(
    offset: int = 0,
    limit: int = 50,
    role: Optional[str] = None,
    user: User = Depends(RoleChecker(UserRole.ADMIN)),
):
    """
    List all users (admin only).
    """
    auth = get_auth_service()

    role_filter = UserRole(role) if role else None
    users = auth.storage.list_users(offset=offset, limit=limit, role=role_filter)

    return {
        "users": [u.to_dict() for u in users],
        "offset": offset,
        "limit": limit,
    }


@router.patch("/users/{user_id}/role")
async def update_user_role(
    user_id: str,
    role: str,
    admin: User = Depends(RoleChecker(UserRole.ADMIN)),
):
    """
    Update user role (admin only).
    """
    auth = get_auth_service()

    target_user = auth.get_user(user_id)
    if not target_user:
        raise HTTPException(status_code=404, detail="User not found")

    try:
        target_user.role = UserRole(role)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid role: {role}")

    auth.storage.update_user(target_user)

    return {"success": True, "user": target_user.to_dict()}


@router.post("/users/{user_id}/deactivate")
async def deactivate_user(
    user_id: str,
    admin: User = Depends(RoleChecker(UserRole.ADMIN)),
):
    """
    Deactivate a user (admin only).
    """
    auth = get_auth_service()

    target_user = auth.get_user(user_id)
    if not target_user:
        raise HTTPException(status_code=404, detail="User not found")

    if target_user.id == admin.id:
        raise HTTPException(status_code=400, detail="Cannot deactivate yourself")

    target_user.is_active = False
    auth.storage.update_user(target_user)

    # Revoke all sessions
    auth.logout_all(user_id)

    return {"success": True}


@router.post("/users/{user_id}/activate")
async def activate_user(
    user_id: str,
    admin: User = Depends(RoleChecker(UserRole.ADMIN)),
):
    """
    Activate a user (admin only).
    """
    auth = get_auth_service()

    target_user = auth.get_user(user_id)
    if not target_user:
        raise HTTPException(status_code=404, detail="User not found")

    target_user.is_active = True
    auth.storage.update_user(target_user)

    return {"success": True}
