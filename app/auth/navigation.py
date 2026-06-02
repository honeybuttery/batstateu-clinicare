"""Shared role-based navigation helpers."""

from __future__ import annotations

from flask import session, url_for


ROLE_HOME_ENDPOINTS: dict[str, str] = {
    "patient_user": "patient.dashboard_page",
    "clinic_nurse": "nurse.dashboard_page",
    "physician": "physician.dashboard_page",
    "clinic_admin": "clinic_admin.dashboard_page",
    "system_admin": "system_admin.dashboard_page",
}


def get_role_home_endpoint(role_name: str | None) -> str:
    """Return default endpoint for a role."""
    if role_name and role_name in ROLE_HOME_ENDPOINTS:
        return ROLE_HOME_ENDPOINTS[role_name]
    return "patient.home"


def get_current_user_home_url() -> str:
    """Resolve a user home URL based on current session role."""
    role_name = session.get("role_name")
    endpoint = get_role_home_endpoint(role_name)
    return url_for(endpoint)
