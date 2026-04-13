"""
SharePoint Innovation Use Log Logger
Logs Start Session / End Session events to the BaseCampApps SharePoint list
using app-only (client credentials) permissions via Microsoft Graph API.
"""

import os
import threading
from datetime import datetime, timezone

import msal
import requests


class SharePointLogger:
    GRAPH_BASE = "https://graph.microsoft.com/v1.0"
    SCOPE = ["https://graph.microsoft.com/.default"]
    SITE_PATH = "peakcampus.sharepoint.com:/sites/BaseCampApps"
    LIST_NAME = "Innovation Use Log"
    APPLICATION_NAME = "AI Boost"

    # Cache resolved IDs for the lifetime of the process
    _site_id = None
    _list_id = None

    def __init__(self):
        self.client_id = os.environ.get("AZURE_AD_CLIENT_ID", "")
        self.client_secret = os.environ.get("AZURE_AD_CLIENT_SECRET", "")
        self.tenant_id = os.environ.get("AZURE_AD_TENANT_ID", "")
        self.env = os.environ.get("FLASK_ENV", "production")
        self.env_label = "Dev" if self.env == "development" else "Prod"

    def is_configured(self):
        return bool(self.client_id and self.client_secret and self.tenant_id)

    def _get_token(self):
        app = msal.ConfidentialClientApplication(
            self.client_id,
            authority=f"https://login.microsoftonline.com/{self.tenant_id}",
            client_credential=self.client_secret,
        )
        result = app.acquire_token_for_client(scopes=self.SCOPE)
        if "access_token" not in result:
            raise ValueError(result.get("error_description", "Failed to acquire token"))
        return result["access_token"]

    def _get_site_id(self, token):
        if SharePointLogger._site_id:
            return SharePointLogger._site_id
        resp = requests.get(
            f"{self.GRAPH_BASE}/sites/{self.SITE_PATH}",
            headers={"Authorization": f"Bearer {token}"},
            timeout=10,
        )
        resp.raise_for_status()
        SharePointLogger._site_id = resp.json()["id"]
        return SharePointLogger._site_id

    def _get_list_id(self, token, site_id):
        if SharePointLogger._list_id:
            return SharePointLogger._list_id
        resp = requests.get(
            f"{self.GRAPH_BASE}/sites/{site_id}/lists",
            headers={"Authorization": f"Bearer {token}"},
            params={"$filter": f"displayName eq '{self.LIST_NAME}'"},
            timeout=10,
        )
        resp.raise_for_status()
        items = resp.json().get("value", [])
        if not items:
            raise ValueError(f"SharePoint list '{self.LIST_NAME}' not found")
        SharePointLogger._list_id = items[0]["id"]
        return SharePointLogger._list_id

    def _write_log(self, activity_type, user_email, user_name, session_id):
        """Does the actual Graph API call — runs in a background thread."""
        try:
            token = self._get_token()
            site_id = self._get_site_id(token)
            list_id = self._get_list_id(token, site_id)

            fields = {
                "UserEmail": user_email,
                "UserName": user_name,
                "LoginTimestamp": datetime.now(timezone.utc).isoformat(),
                "UserRole": "user",
                "ActivityType": activity_type,
                "Application": self.APPLICATION_NAME,
                "SessionID": session_id,
                "Env": self.env_label,
                "Status": "Successful",
            }

            resp = requests.post(
                f"{self.GRAPH_BASE}/sites/{site_id}/lists/{list_id}/items",
                headers={
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json",
                },
                json={"fields": fields},
                timeout=10,
            )
            resp.raise_for_status()
            print(f"[SharePoint] Logged '{activity_type}' for {user_email}")
        except Exception as e:
            print(f"[SharePoint] Logging failed for '{activity_type}': {e}")

    def log(self, activity_type, user_email, user_name, session_id):
        """Fire-and-forget: logs in a background thread so it doesn't block the response."""
        if not self.is_configured():
            print("[SharePoint] Skipping log — Azure AD not configured.")
            return
        thread = threading.Thread(
            target=self._write_log,
            args=(activity_type, user_email, user_name, session_id),
            daemon=True,
        )
        thread.start()


# Module-level singleton
logger = SharePointLogger()
