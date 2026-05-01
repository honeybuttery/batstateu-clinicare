"""Display-only label formatting helpers."""

from __future__ import annotations


_LABEL_OVERRIDES: dict[str, str] = {
	"configuration_updated": "Configuration Updated",
	"user_created": "User Created",
	"user_updated": "User Updated",
	"lookup_created": "Lookup Added",
	"lookup_updated": "Lookup Updated",
	"login": "Login",
	"failed_login": "Failed Login",
	"system_settings": "System Settings",
	"users": "Users",
	"sessions": "Sessions",
	"lookups": "Lookups",
	"appointments": "Appointments",
	"consultations": "Consultations",
	"reports": "Reports",
	"clinic_admin": "Clinic Admin",
	"system_admin": "System Admin",
	"clinic_nurse": "Clinic Nurse",
	"patient_user": "Patient User",
}


def format_display_label(value: object) -> str:
	"""Convert raw system values into human-readable labels for the UI."""
	if value is None:
		return "-"

	text = str(value).strip()
	if not text:
		return "-"

	lookup_key = text.lower()
	if lookup_key in _LABEL_OVERRIDES:
		return _LABEL_OVERRIDES[lookup_key]

	return text.replace("_", " ").replace("-", " ").title()