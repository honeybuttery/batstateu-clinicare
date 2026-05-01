"""System admin routes."""

from __future__ import annotations

import mysql.connector
from flask import Blueprint, current_app, flash, redirect, render_template, request, session, url_for
from werkzeug.security import generate_password_hash

from app.auth.decorators import login_required, role_required
from app.db.repositories.lookup_repository import (
	create_lookup_value,
	get_lookup_value,
	list_lookup_values,
	update_lookup_value,
)
from app.db.repositories.user_repository import (
	create_user,
	get_user_by_id,
	list_roles,
	list_users,
	update_user,
)
from app.services.audit_service import get_audit_logs_for_system_admin, log_audit_event
from app.services.system_settings_service import (
	get_configuration_values,
	save_configuration_values,
)

bp = Blueprint("system_admin", __name__)


@bp.get("/system-admin/users")
@login_required
@role_required("system_admin")
def users_list_page():
	"""Show user accounts with role and status."""
	try:
		users = list_users()
	except mysql.connector.Error:
		flash("Database is unavailable. Please try again later.", "danger")
		users = []

	return render_template(
		"system_admin/users_list.html",
		page_title="Users",
		users=users,
	)


@bp.get("/system-admin/users/new")
@login_required
@role_required("system_admin")
def user_create_page():
	"""Open user create form."""
	return render_template(
		"system_admin/user_form.html",
		page_title="Create User",
		user=None,
		roles=list_roles(),
	)


@bp.post("/system-admin/users/new")
@login_required
@role_required("system_admin")
def user_create_submit():
	"""Create a user account."""
	admin_user_id = int(session["user_id"])
	ip_address = request.remote_addr or "127.0.0.1"

	email = (request.form.get("institutional_email") or "").strip().lower()
	password = (request.form.get("password") or "").strip()
	role_id = request.form.get("role_id", type=int)
	account_status = (request.form.get("account_status") or "pending_verification").strip()

	if not email or not password or not role_id:
		flash("Email, password, and role are required.", "danger")
		return redirect(url_for("system_admin.user_create_page"))

	try:
		new_id = create_user(
			institutional_email=email,
			password_hash=generate_password_hash(password),
			role_id=role_id,
			account_status=account_status,
		)
		log_audit_event(
			user_id=admin_user_id,
			action_type="user_created",
			entity_type="users",
			entity_id=new_id,
			description=f"System admin created user {email}.",
			ip_address=ip_address,
		)
	except mysql.connector.Error as exc:
		flash(str(exc), "danger")
		return redirect(url_for("system_admin.user_create_page"))

	flash("User created.", "success")
	return redirect(url_for("system_admin.users_list_page"))


@bp.get("/system-admin/users/<int:user_id>/edit")
@login_required
@role_required("system_admin")
def user_edit_page(user_id: int):
	"""Open user edit form."""
	try:
		user = get_user_by_id(user_id)
	except mysql.connector.Error:
		flash("Database is unavailable. Please try again later.", "danger")
		return redirect(url_for("system_admin.users_list_page"))

	if not user:
		flash("User not found.", "warning")
		return redirect(url_for("system_admin.users_list_page"))

	return render_template(
		"system_admin/user_form.html",
		page_title="Edit User",
		user=user,
		roles=list_roles(),
	)


@bp.post("/system-admin/users/<int:user_id>/edit")
@login_required
@role_required("system_admin")
def user_edit_submit(user_id: int):
	"""Update user account, role, and status."""
	admin_user_id = int(session["user_id"])
	ip_address = request.remote_addr or "127.0.0.1"

	email = (request.form.get("institutional_email") or "").strip().lower()
	role_id = request.form.get("role_id", type=int)
	account_status = (request.form.get("account_status") or "pending_verification").strip()
	new_password = (request.form.get("password") or "").strip()

	if not email or not role_id:
		flash("Email and role are required.", "danger")
		return redirect(url_for("system_admin.user_edit_page", user_id=user_id))

	try:
		updated = update_user(
			user_id=user_id,
			institutional_email=email,
			role_id=role_id,
			account_status=account_status,
			password_hash=generate_password_hash(new_password) if new_password else None,
		)
		if updated:
			log_audit_event(
				user_id=admin_user_id,
				action_type="user_updated",
				entity_type="users",
				entity_id=user_id,
				description=f"System admin updated user_id={user_id}.",
				ip_address=ip_address,
			)
	except mysql.connector.Error as exc:
		flash(str(exc), "danger")
		return redirect(url_for("system_admin.user_edit_page", user_id=user_id))

	if not updated:
		flash("User not found.", "warning")
		return redirect(url_for("system_admin.users_list_page"))

	flash("User updated.", "success")
	return redirect(url_for("system_admin.users_list_page"))


@bp.get("/system-admin/lookups")
@login_required
@role_required("system_admin")
def lookups_list_page():
	"""Show lookup values for triage or consultation types."""
	lookup_type = (request.args.get("type") or "triage").strip().lower()
	if lookup_type not in {"triage", "consultation"}:
		lookup_type = "triage"

	try:
		rows = list_lookup_values(lookup_type)
	except (mysql.connector.Error, ValueError) as exc:
		flash(str(exc), "danger")
		rows = []

	return render_template(
		"system_admin/lookups_list.html",
		page_title="Lookup Management",
		lookup_type=lookup_type,
		rows=rows,
	)


@bp.get("/system-admin/lookups/<string:lookup_type>/new")
@login_required
@role_required("system_admin")
def lookup_create_page(lookup_type: str):
	"""Open lookup create form."""
	return render_template(
		"system_admin/lookup_form.html",
		page_title="Create Lookup Value",
		lookup_type=lookup_type,
		item=None,
	)


@bp.post("/system-admin/lookups/<string:lookup_type>/new")
@login_required
@role_required("system_admin")
def lookup_create_submit(lookup_type: str):
	"""Create lookup value."""
	admin_user_id = int(session["user_id"])
	ip_address = request.remote_addr or "127.0.0.1"

	code = (request.form.get("code") or "").strip()
	display_name = (request.form.get("display_name") or "").strip()
	is_active = request.form.get("is_active") == "1"

	if not code or not display_name:
		flash("Code and display name are required.", "danger")
		return redirect(url_for("system_admin.lookup_create_page", lookup_type=lookup_type))

	try:
		new_id = create_lookup_value(
			lookup_type=lookup_type,
			code=code,
			display_name=display_name,
			is_active=is_active,
		)
		log_audit_event(
			user_id=admin_user_id,
			action_type="lookup_created",
			entity_type=f"lookup_{lookup_type}",
			entity_id=new_id,
			description=f"Created lookup value {code} ({display_name}).",
			ip_address=ip_address,
		)
	except (mysql.connector.Error, ValueError) as exc:
		flash(str(exc), "danger")
		return redirect(url_for("system_admin.lookup_create_page", lookup_type=lookup_type))

	flash("Lookup value created.", "success")
	return redirect(url_for("system_admin.lookups_list_page", type=lookup_type))


@bp.get("/system-admin/lookups/<string:lookup_type>/<int:lookup_id>/edit")
@login_required
@role_required("system_admin")
def lookup_edit_page(lookup_type: str, lookup_id: int):
	"""Open lookup edit form."""
	try:
		item = get_lookup_value(lookup_type, lookup_id)
	except (mysql.connector.Error, ValueError) as exc:
		flash(str(exc), "danger")
		return redirect(url_for("system_admin.lookups_list_page", type="triage"))

	if not item:
		flash("Lookup item not found.", "warning")
		return redirect(url_for("system_admin.lookups_list_page", type=lookup_type))

	return render_template(
		"system_admin/lookup_form.html",
		page_title="Edit Lookup Value",
		lookup_type=lookup_type,
		item=item,
	)


@bp.post("/system-admin/lookups/<string:lookup_type>/<int:lookup_id>/edit")
@login_required
@role_required("system_admin")
def lookup_edit_submit(lookup_type: str, lookup_id: int):
	"""Update lookup value."""
	admin_user_id = int(session["user_id"])
	ip_address = request.remote_addr or "127.0.0.1"

	code = (request.form.get("code") or "").strip()
	display_name = (request.form.get("display_name") or "").strip()
	is_active = request.form.get("is_active") == "1"

	if not code or not display_name:
		flash("Code and display name are required.", "danger")
		return redirect(url_for("system_admin.lookup_edit_page", lookup_type=lookup_type, lookup_id=lookup_id))

	try:
		updated = update_lookup_value(
			lookup_type=lookup_type,
			lookup_id=lookup_id,
			code=code,
			display_name=display_name,
			is_active=is_active,
		)
		if updated:
			log_audit_event(
				user_id=admin_user_id,
				action_type="lookup_updated",
				entity_type=f"lookup_{lookup_type}",
				entity_id=lookup_id,
				description=f"Updated lookup value {code} ({display_name}).",
				ip_address=ip_address,
			)
	except (mysql.connector.Error, ValueError) as exc:
		flash(str(exc), "danger")
		return redirect(url_for("system_admin.lookup_edit_page", lookup_type=lookup_type, lookup_id=lookup_id))

	if not updated:
		flash("Lookup item not found.", "warning")
		return redirect(url_for("system_admin.lookups_list_page", type=lookup_type))

	flash("Lookup value updated.", "success")
	return redirect(url_for("system_admin.lookups_list_page", type=lookup_type))


@bp.get("/system-admin/configuration")
@bp.post("/system-admin/configuration")
@login_required
@role_required("system_admin")
def configuration_page():
	"""Persistent configuration page for system-wide settings."""
	if request.method == "POST":
		reports_default_days = request.form.get("reports_default_days", "30")
		audit_log_limit = request.form.get("audit_log_limit", "300")
		allowed_email_domains = request.form.get("allowed_email_domains", "")

		try:
			save_configuration_values(
				reports_default_days=reports_default_days,
				audit_log_limit=audit_log_limit,
				allowed_email_domains=allowed_email_domains,
			)
			log_audit_event(
				user_id=int(session["user_id"]),
				action_type="configuration_updated",
				entity_type="system_settings",
				entity_id=None,
				description="System settings were updated by system admin.",
				ip_address=request.remote_addr or "127.0.0.1",
			)
		except mysql.connector.Error as exc:
			flash(str(exc), "danger")
			return redirect(url_for("system_admin.configuration_page"))

		flash("Configuration saved.", "success")
		return redirect(url_for("system_admin.configuration_page"))

	try:
		config_values = get_configuration_values(current_app.config.get("APP_NAME", "BatStateU CliniCare"))
	except mysql.connector.Error:
		flash("Database is unavailable. Showing defaults.", "warning")
		config_values = {
			"app_name": current_app.config.get("APP_NAME", "BatStateU CliniCare"),
			"reports_default_days": "30",
			"audit_log_limit": "300",
			"allowed_email_domains": "batstate-u.edu.ph,g.batstate-u.edu.ph",
		}

	return render_template(
		"system_admin/configuration.html",
		page_title="Configuration",
		config_values=config_values,
	)


@bp.get("/system-admin/audit-logs")
@login_required
@role_required("system_admin")
def audit_logs_page():
	"""Full audit log view for system admin."""
	# read filter query params (defaults match UI requirements)
	showing = (request.args.get("showing") or "all").strip()
	date_range = (request.args.get("date") or "last_30_days").strip()
	action = (request.args.get("action") or "all").strip()
	entity = (request.args.get("entity") or "all").strip()
	
	# map form values to internal keys
	showing_map = {
		"all": None,
		"all_audit_logs": None,
		"login_activity": "login_activity",
		"user_changes": "user_changes",
		"lookup_changes": "lookup_changes",
		"configuration_changes": "configuration_changes",
		"failed_actions": "failed_actions",
		"my_activity": "my_activity",
	}
	action_map = {
		"all": None,
		"all_actions": None,
		"login": "login",
		"create": "create",
		"update": "update",
		"delete": "delete",
		"failed_login": "failed_login",
	}
	entity_map = {
		"all": None,
		"all_entities": None,
		"users": "users",
		"sessions": "sessions",
		"lookups": "lookups",
		"configuration": "configuration",
		"appointments": "appointments",
		"consultations": "consultations",
		"reports": "reports",
	}

	mapped_showing = showing_map.get(showing, None)
	mapped_action = action_map.get(action, None)
	mapped_entity = entity_map.get(entity, None)

	try:
		# if showing == my_activity, provide user_id
		user_id = session.get("user_id") if mapped_showing == "my_activity" else None
		result = get_audit_logs_for_system_admin(
			limit=500,
			showing=mapped_showing,
			date_range=date_range,
			action=mapped_action,
			entity=mapped_entity,
			user_id=user_id,
		)
	except mysql.connector.Error:
		flash("Database is unavailable. Please try again later.", "danger")
		result = {"scope": "full", "logs": []}

	# pass current filter selections back to template for defaults
	return render_template(
		"clinic_admin/audit_logs.html",
		page_title="Audit Logs (System Admin)",
		logs=result["logs"],
		scope=result.get("scope", "full"),
		filters={
			"showing": showing,
			"date": date_range,
			"action": action,
			"entity": entity,
		},
	)
