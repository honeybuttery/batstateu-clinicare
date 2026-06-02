"""Clinic admin routes."""

from __future__ import annotations

import mysql.connector
from flask import Blueprint, flash, redirect, render_template, request, url_for

from app.auth.decorators import login_required, role_required
from app.db.repositories.report_repository import (
	get_deidentified_report,
	get_operations_summary,
	list_available_reports,
)
from app.services.audit_service import get_audit_logs_for_clinic_admin

bp = Blueprint("clinic_admin", __name__)


@bp.get("/clinic-admin/dashboard")
@login_required
@role_required("clinic_admin")
def dashboard_page():
	"""Clinic admin dashboard with high-level operations summary."""
	try:
		summary = get_operations_summary()
		reports = list_available_reports()
		recent_activity = get_audit_logs_for_clinic_admin(limit=8)["logs"]
	except mysql.connector.Error:
		flash("Database is unavailable. Please try again later.", "danger")
		summary = {}
		reports = []
		recent_activity = []

	return render_template(
		"clinic_admin/dashboard.html",
		page_title="Clinic Admin Dashboard",
		summary=summary,
		reports=reports,
		recent_activity=recent_activity,
	)


@bp.get("/clinic-admin/operations")
@login_required
@role_required("clinic_admin")
def operations_overview_page():
	"""Clinic admin overview page."""
	try:
		summary = get_operations_summary()
	except mysql.connector.Error:
		flash("Database is unavailable. Please try again later.", "danger")
		summary = {}

	return render_template(
		"clinic_admin/operations_overview.html",
		page_title="Overview",
		summary=summary,
	)


@bp.get("/clinic-admin/reports")
@login_required
@role_required("clinic_admin")
def reports_page():
	"""List de-identified report options."""
	return render_template(
		"clinic_admin/reports.html",
		page_title="De-identified Reports",
		reports=list_available_reports(),
	)


@bp.get("/clinic-admin/reports/<string:report_key>")
@login_required
@role_required("clinic_admin")
def report_detail_page(report_key: str):
	"""Show one de-identified report output table."""
	try:
		report = get_deidentified_report(report_key)
	except mysql.connector.Error:
		flash("Database is unavailable. Please try again later.", "danger")
		return redirect(url_for("clinic_admin.reports_page"))

	if not report:
		flash("Report not found.", "warning")
		return redirect(url_for("clinic_admin.reports_page"))

	return render_template(
		"clinic_admin/report_detail.html",
		page_title=report["title"],
		report=report,
	)


@bp.get("/clinic-admin/audit-logs")
@login_required
@role_required("clinic_admin")
def audit_logs_page():
	"""Read-only de-identified audit logs for clinic admin scope."""
	filters = {
		"showing": (request.args.get("showing") or "all").strip().lower(),
		"date": (request.args.get("date") or "last_30_days").strip().lower(),
		"action": (request.args.get("action") or "all").strip().lower(),
		"entity": (request.args.get("entity") or "all").strip().lower(),
	}

	try:
		result = get_audit_logs_for_clinic_admin(
			limit=200,
			showing=filters["showing"],
			date_range=filters["date"],
			action=filters["action"],
			entity=filters["entity"],
		)
	except mysql.connector.Error:
		flash("Database is unavailable. Please try again later.", "danger")
		result = {"scope": "deidentified", "logs": []}

	return render_template(
		"clinic_admin/audit_logs.html",
		page_title="Audit Logs",
		logs=result["logs"],
		scope=result["scope"],
		filters=filters,
	)
