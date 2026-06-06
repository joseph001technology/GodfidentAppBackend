from django.utils import timezone
from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string
from datetime import timedelta
import logging

from .models import User, EmailVerificationToken, PasswordResetToken, AuditLog

logger = logging.getLogger(__name__)

TOKEN_EXPIRY_HOURS = 24
PASSWORD_RESET_EXPIRY_HOURS = 1


def create_verification_token(user: User) -> EmailVerificationToken:
    """Create a new email verification token, invalidating old ones."""
    EmailVerificationToken.objects.filter(user=user, is_used=False).update(is_used=True)
    token = EmailVerificationToken.objects.create(
        user=user,
        expires_at=timezone.now() + timedelta(hours=TOKEN_EXPIRY_HOURS),
    )
    return token


def send_verification_email(user: User, token: EmailVerificationToken) -> None:
    """Send verification email to user."""
    verify_url = f"{settings.FRONTEND_URL}/verify-email?token={token.token}"
    subject = 'Verify your Godfident account'
    message = (
        f"Hello {user.first_name or user.email},\n\n"
        f"Please verify your email address by clicking the link below:\n\n"
        f"{verify_url}\n\n"
        f"This link expires in {TOKEN_EXPIRY_HOURS} hours.\n\n"
        f"If you did not create this account, please ignore this email.\n\n"
        f"God bless,\nThe Godfident Team"
    )
    try:
        send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [user.email])
    except Exception as e:
        logger.error(f"Failed to send verification email to {user.email}: {e}")


def verify_email_token(token_str: str) -> tuple[bool, str]:
    """Verify an email token. Returns (success, message)."""
    try:
        token = EmailVerificationToken.objects.select_related('user').get(token=token_str)
    except EmailVerificationToken.DoesNotExist:
        return False, 'Invalid verification token.'

    if not token.is_valid():
        return False, 'This verification link has expired or already been used.'

    token.is_used = True
    token.save()
    token.user.is_email_verified = True
    token.user.save(update_fields=['is_email_verified'])

    log_action(token.user, 'EMAIL_VERIFIED')
    return True, 'Email verified successfully.'


def create_password_reset_token(email: str) -> tuple[bool, str]:
    """Create password reset token. Returns (success, message)."""
    try:
        user = User.objects.get(email=email, is_active=True)
    except User.DoesNotExist:
        # Don't reveal whether email exists
        return True, 'If this email exists, a reset link has been sent.'

    PasswordResetToken.objects.filter(user=user, is_used=False).update(is_used=True)
    token = PasswordResetToken.objects.create(
        user=user,
        expires_at=timezone.now() + timedelta(hours=PASSWORD_RESET_EXPIRY_HOURS),
    )

    reset_url = f"{settings.FRONTEND_URL}/reset-password?token={token.token}"
    subject = 'Reset your Godfident password'
    message = (
        f"Hello {user.first_name or user.email},\n\n"
        f"You requested a password reset. Click the link below:\n\n"
        f"{reset_url}\n\n"
        f"This link expires in {PASSWORD_RESET_EXPIRY_HOURS} hour(s).\n\n"
        f"If you did not request this, please ignore this email.\n\n"
        f"God bless,\nThe Godfident Team"
    )
    try:
        send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [user.email])
    except Exception as e:
        logger.error(f"Failed to send reset email to {user.email}: {e}")

    log_action(user, 'PASSWORD_RESET_REQUESTED')
    return True, 'If this email exists, a reset link has been sent.'


def reset_password(token_str: str, new_password: str) -> tuple[bool, str]:
    """Reset password using token. Returns (success, message)."""
    try:
        token = PasswordResetToken.objects.select_related('user').get(token=token_str)
    except PasswordResetToken.DoesNotExist:
        return False, 'Invalid or expired reset token.'

    if not token.is_valid():
        return False, 'This reset link has expired or already been used.'

    token.is_used = True
    token.save()
    token.user.set_password(new_password)
    token.user.save(update_fields=['password'])

    log_action(token.user, 'PASSWORD_RESET_COMPLETED')
    return True, 'Password reset successfully.'


def log_action(user, action: str, request=None, metadata: dict = None) -> None:
    """Log a security-relevant user action."""
    ip_address = None
    user_agent = ''
    if request:
        ip_address = get_client_ip(request)
        user_agent = request.META.get('HTTP_USER_AGENT', '')

    AuditLog.objects.create(
        user=user,
        action=action,
        ip_address=ip_address,
        user_agent=user_agent,
        metadata=metadata or {},
    )


def get_client_ip(request) -> str:
    """Extract real IP from request."""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        return x_forwarded_for.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR', '')
