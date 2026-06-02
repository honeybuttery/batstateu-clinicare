"""Clinic schedule validation helpers."""

from __future__ import annotations

from datetime import datetime, time


def validate_clinic_schedule(date_str: str | None, time_str: str | None) -> tuple[bool, str]:
	"""Validate schedule against clinic hours (Mon-Fri, 08:00-17:00)."""
	if not date_str and not time_str:
		return True, ""
	if not date_str or not time_str:
		return False, "Please provide both a preferred date and time."

	try:
		date_value = datetime.strptime(date_str, "%Y-%m-%d").date()
	except ValueError:
		return False, "Preferred date is invalid."

	try:
		time_value = datetime.strptime(time_str, "%H:%M").time()
	except ValueError:
		try:
			time_value = datetime.strptime(time_str, "%H:%M:%S").time()
		except ValueError:
			return False, "Preferred time is invalid."

	# Monday is 0, Sunday is 6
	if date_value.weekday() > 4:
		return False, "Clinic is closed on weekends. Please select a weekday."

	open_time = time(8, 0)
	close_time = time(17, 0)
	if time_value < open_time or time_value >= close_time:
		return False, "Clinic hours are Mon-Fri, 8:00 AM to 5:00 PM."

	return True, ""