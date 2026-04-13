"""
Auth Blueprint — /auth/login, /auth/callback, /auth/logout
"""

import uuid
from flask import Blueprint, redirect, request, session
from .auth_helper import AzureADAuth
from sharepoint_logger import logger as sp_logger

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')


@auth_bp.route('/login')
def login():
    """Redirect the user to the Microsoft login page."""
    # Remember where to send them after login
    next_url = request.args.get('next', '/')
    session['next'] = next_url

    auth = AzureADAuth()
    if not auth.is_configured():
        return (
            "Azure AD is not configured. "
            "Set AZURE_AD_CLIENT_ID, AZURE_AD_CLIENT_SECRET, "
            "AZURE_AD_TENANT_ID, and AZURE_AD_REDIRECT_URI.",
            500,
        )

    return redirect(auth.get_auth_url())


@auth_bp.route('/callback')
def callback():
    """Handle the OAuth 2.0 callback from Microsoft."""
    if 'error' in request.args:
        error_desc = request.args.get('error_description', request.args.get('error'))
        return f"Authentication failed: {error_desc}", 400

    code = request.args.get('code')
    if not code:
        return "No authorization code received.", 400

    auth = AzureADAuth()
    try:
        auth.get_token_from_code(code)
    except ValueError as e:
        return f"Token exchange failed: {e}", 500

    # Generate a session ID for logging
    session_id = str(uuid.uuid4())
    session['log_session_id'] = session_id

    user = session.get('user', {})
    sp_logger.log(
        activity_type="Start Session",
        user_email=user.get('email', ''),
        user_name=user.get('name', ''),
        session_id=session_id,
    )

    next_url = session.pop('next', '/')
    return redirect(next_url)


@auth_bp.route('/logout')
def logout():
    """Clear the session and redirect to Microsoft single-sign-out."""
    auth = AzureADAuth()
    post_logout_uri = request.host_url.rstrip('/')

    user = session.get('user', {})
    session_id = session.get('log_session_id', '')
    sp_logger.log(
        activity_type="End Session",
        user_email=user.get('email', ''),
        user_name=user.get('name', ''),
        session_id=session_id,
    )

    session.clear()
    return redirect(auth.get_logout_url(post_logout_uri))
