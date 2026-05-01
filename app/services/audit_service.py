"""Audit service helpers."""

from __future__ import annotations

from typing import Any
from datetime import datetime, timedelta

from app.db.connection import get_db_cursor
from app.db.repositories.audit_repository import (
	list_audit_logs,
	list_audit_logs_deidentified,
)


def log_audit_event(
	*,
	user_id: int,
	action_type: str,
	entity_type: str,
	entity_id: int | None,
	description: str | None,
	ip_address: str | None,
) -> None:
	"""Write an audit log row using the current DB connection helper."""
	with get_db_cursor() as cur:
		cur.execute(
			"""
			INSERT INTO audit_logs (
				user_id,
				action_type,
				entity_type,
				entity_id,
				description,
				performed_at,
				ip_address
			) VALUES (%s, %s, %s, %s, %s, UTC_TIMESTAMP(), %s)
			""",
			(user_id, action_type, entity_type, entity_id, description, ip_address),
		)


def get_audit_logs_for_system_admin(
	*,
	limit: int = 300,
	showing: str | None = None,
	date_range: str | None = None,
	action: str | None = None,
	entity: str | None = None,
	user_id: int | None = None,
) -> dict[str, Any]:
	"""Return audit logs for system admin with optional filters.

	- `showing` maps to higher-level categories (login, user_changes, lookup_changes, configuration_changes, failed, my_activity)
	- `date_range` may be: today, last_7_days, last_30_days, custom
	"""
	# compute date_from/date_to defaults
	date_from = None
	date_to = None
	now = datetime.utcnow()
	if date_range in (None, "last_30_days"):
		date_from = (now - timedelta(days=30)).strftime("%Y-%m-%d 00:00:00")
		date_to = now.strftime("%Y-%m-%d 23:59:59")
	elif date_range == "today":
		date_from = now.strftime("%Y-%m-%d 00:00:00")
		date_to = now.strftime("%Y-%m-%d 23:59:59")
	elif date_range == "last_7_days":
		date_from = (now - timedelta(days=7)).strftime("%Y-%m-%d 00:00:00")
		date_to = now.strftime("%Y-%m-%d 23:59:59")

	# map showing to action/entity/user filters
	mapped_action = None
	mapped_action_like = None
	mapped_entity = None
	mapped_user_id = None

	if showing == "login_activity":
		# show login/logout actions
		# the action dropdown can further limit
		mapped_action = None
	elif showing == "user_changes":
		mapped_action = None
		mapped_entity = "users"
	elif showing == "lookup_changes":
		mapped_entity = "lookups"
	elif showing == "configuration_changes":
		mapped_entity = "configuration"
	elif showing == "failed_actions":
		# 'failed' handled via action filter below when set to 'failed'
		mapped_action = None
	elif showing == "my_activity":
		mapped_user_id = user_id

	# Action mapping for common choices
	if action == "login":
		mapped_action = "login"
	elif action == "create":
		mapped_action_like = "%created%"
	elif action == "update":
		mapped_action_like = "%updated%"
	elif action == "delete":
		mapped_action_like = "%deleted%"
	elif action == "failed_login":
		mapped_action = "failed_login"

	try:
		logs = list_audit_logs(
			limit=limit,
			action=mapped_action,
			action_like=mapped_action_like,
			entity=mapped_entity,
			date_from=date_from,
			date_to=date_to,
			user_id=mapped_user_id,
		)
	except Exception:
		return {"ok": False, "scope": "full", "logs": []}

	return {"ok": True, "scope": "full", "logs": logs}


def get_audit_logs_for_clinic_admin(limit: int = 200) -> dict[str, Any]:
	return {
		"ok": True,
		"scope": "deidentified",
		"logs": list_audit_logs_deidentified(limit=limit),
	}
