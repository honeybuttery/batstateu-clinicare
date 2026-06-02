"""Display-only label formatting helpers."""

from __future__ import annotations

from datetime import datetime, timedelta


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


def format_time_12h(value: object) -> str:
	"""Convert time strings to 12-hour display (e.g., 13:00 -> 1:00 PM)."""
	if value is None:
		return "-"

	text = str(value).strip()
	if not text:
		return "-"

	for fmt in ("%H:%M:%S", "%H:%M"):
		try:
			parsed = datetime.strptime(text, fmt)
			hour = parsed.hour % 12 or 12
			minute = parsed.minute
			suffix = "AM" if parsed.hour < 12 else "PM"
			return f"{hour}:{minute:02d} {suffix}"
		except ValueError:
			continue

	return text


def format_local_datetime(value: object, offset_hours: int = 8) -> str:
	"""Convert naive UTC datetime strings to local time using a fixed offset."""
	if value is None:
		return "-"

	text = str(value).strip()
	if not text:
		return "-"

	for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M:%S.%f"):
		try:
			parsed = datetime.strptime(text, fmt)
			local_dt = parsed + timedelta(hours=offset_hours)
			return local_dt.strftime("%Y-%m-%d %H:%M:%S")
		except ValueError:
			continue

	return text