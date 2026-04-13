"""
Azure AD Authentication Helper
OAuth 2.0 Authorization Code Flow using MSAL
"""

import os
import msal
from flask import session


class AzureADAuth:
    def __init__(self):
        self.client_id = os.environ.get('AZURE_AD_CLIENT_ID', '')
        self.client_secret = os.environ.get('AZURE_AD_CLIENT_SECRET', '')
        self.tenant_id = os.environ.get('AZURE_AD_TENANT_ID', '')
        self.redirect_uri = os.environ.get('AZURE_AD_REDIRECT_URI', '')
        self.authority = f"https://login.microsoftonline.com/{self.tenant_id}"
        self.scopes = ['User.Read']

    def is_configured(self):
        """Return True if all required Azure AD env vars are set."""
        return bool(
            self.client_id
            and self.client_secret
            and self.tenant_id
            and self.redirect_uri
        )

    def _get_msal_app(self, token_cache_str=None):
        """Build a ConfidentialClientApplication, optionally restoring a token cache."""
        cache = msal.SerializableTokenCache()
        if token_cache_str:
            cache.deserialize(token_cache_str)

        app = msal.ConfidentialClientApplication(
            self.client_id,
            authority=self.authority,
            client_credential=self.client_secret,
            token_cache=cache,
        )
        return app, cache

    def get_auth_url(self):
        """Return the Microsoft login URL to redirect the user to."""
        msal_app, _ = self._get_msal_app()
        return msal_app.get_authorization_request_url(
            self.scopes,
            redirect_uri=self.redirect_uri,
        )

    def get_token_from_code(self, code):
        """Exchange authorization code for tokens and populate Flask session."""
        msal_app, cache = self._get_msal_app(session.get('token_cache'))
        result = msal_app.acquire_token_by_authorization_code(
            code,
            scopes=self.scopes,
            redirect_uri=self.redirect_uri,
        )

        if 'error' in result:
            raise ValueError(
                result.get('error_description') or result.get('error', 'Unknown error')
            )

        claims = result.get('id_token_claims', {})
        session['authenticated'] = True
        session['user'] = {
            'name': claims.get('name', ''),
            'email': (
                claims.get('preferred_username')
                or claims.get('upn')
                or claims.get('email', '')
            ).lower(),
            'id': claims.get('oid', ''),
        }
        session['access_token'] = result.get('access_token', '')
        session['token_cache'] = cache.serialize()
        return result

    def get_logout_url(self, post_logout_redirect_uri):
        """Return the Microsoft single-sign-out URL."""
        return (
            f"{self.authority}/oauth2/v2.0/logout"
            f"?post_logout_redirect_uri={post_logout_redirect_uri}"
        )
