"""Physician consultation routes."""

from __future__ import annotations

import mysql.connector
from flask import Blueprint, flash, redirect, render_template, request, session, url_for

from app.auth.decorators import login_required, role_required
from app.services.audit_service import log_audit_event
from app.services.visit_workflow_service import (
	get_patient_clinical_history,
	get_physician_queue,
	get_physician_visit_detail,
	save_consultation,
)

bp = Blueprint("physician", __name__)


@bp.get("/physician/dashboard")
@login_required
@role_required("physician")
def dashboard_page():
	"""Redirect to the physician landing page."""
	return redirect(url_for("physician.queue_page"))


@bp.get("/physician/queue")
@login_required
@role_required("physician")
def queue_page():
	"""Show physician visit queue."""
	physician_user_id = int(session["user_id"])
	try:
		result = get_physician_queue(physician_user_id)
	except mysql.connector.Error:
		flash("Database is unavailable. Please try again later.", "danger")
		result = {"queue": []}

	return render_template(
		"physician/queue.html",
		page_title="Physician Queue",
		queue=result["queue"],
	)


@bp.get("/physician/visits/<int:visit_id>")
@login_required
@role_required("physician")
def visit_detail_page(visit_id: int):
	"""Show visit detail with triage + consultation preview."""
	physician_user_id = int(session["user_id"])
	try:
		result = get_physician_visit_detail(physician_user_id, visit_id)
	except mysql.connector.Error:
		flash("Database is unavailable. Please try again later.", "danger")
		return redirect(url_for("physician.queue_page"))

	if not result["ok"]:
		flash(result["message"], "warning")
		return redirect(url_for("physician.queue_page"))

	return render_template(
		"physician/visit_detail.html",
		page_title="Visit Detail",
		visit=result["visit"],
		consultation=result["consultation"],
	)


@bp.get("/physician/visits/<int:visit_id>/consultation")
@login_required
@role_required("physician")
def consultation_form_page(visit_id: int):
	"""Open consultation form."""
	physician_user_id = int(session["user_id"])
	try:
		result = get_physician_visit_detail(physician_user_id, visit_id)
	except mysql.connector.Error:
		flash("Database is unavailable. Please try again later.", "danger")
		return redirect(url_for("physician.queue_page"))

	if not result["ok"]:
		flash(result["message"], "warning")
		return redirect(url_for("physician.queue_page"))

	return render_template(
		"physician/consultation_form.html",
		page_title="Consultation Form",
		visit=result["visit"],
		consultation=result["consultation"],
	)


@bp.post("/physician/visits/<int:visit_id>/consultation")
@login_required
@role_required("physician")
def consultation_form_submit(visit_id: int):
	"""Save consultation record for physician visit."""
	physician_user_id = int(session["user_id"])

	try:
		result = save_consultation(
			physician_user_id=physician_user_id,
			visit_id=visit_id,
			history=(request.form.get("history") or "").strip() or None,
			physical_exam=(request.form.get("physical_exam") or "").strip() or None,
			assessment=(request.form.get("assessment") or "").strip() or None,
			plan=(request.form.get("plan") or "").strip() or None,
			follow_up_instructions=(request.form.get("follow_up_instructions") or "").strip() or None,
		)
	except mysql.connector.Error as exc:
		flash(str(exc), "danger")
		return redirect(url_for("physician.consultation_form_page", visit_id=visit_id))

	if not result["ok"]:
		flash(result["message"], "danger")
		return redirect(url_for("physician.consultation_form_page", visit_id=visit_id))

	try:
		log_audit_event(
			user_id=physician_user_id,
			action_type="consultation_saved",
			entity_type="consultations",
			entity_id=int(result["consultation_id"]),
			description=f"Saved consultation for visit #{visit_id}.",
			ip_address=request.remote_addr or "127.0.0.1",
		)
	except mysql.connector.Error:
		pass

	flash("Consultation saved.", "success")
	return redirect(url_for("physician.visit_detail_page", visit_id=visit_id))




@bp.get("/physician/patients/<int:patient_profile_id>/history")
@login_required
@role_required("physician")
def patient_history_page(patient_profile_id: int):
	"""Show patient consultation history for current physician context."""
	physician_user_id = int(session["user_id"])
	try:
		result = get_patient_clinical_history(physician_user_id, patient_profile_id)
	except mysql.connector.Error:
		flash("Database is unavailable. Please try again later.", "danger")
		return redirect(url_for("physician.queue_page"))

	if not result["ok"]:
		flash(result["message"], "warning")
		return redirect(url_for("physician.queue_page"))

	return render_template(
		"physician/patient_history.html",
		page_title="Patient History",
		patient=result["patient"],
		history=result["history"],
	)
