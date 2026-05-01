"""Nurse appointment review and check-in routes."""

from __future__ import annotations

from datetime import datetime

import mysql.connector
from flask import Blueprint, flash, redirect, render_template, request, session, url_for

from app.auth.decorators import login_required, role_required
from app.services.audit_service import log_audit_event
from app.services.appointment_service import (
	approve_adjust_or_decline_appointment,
	check_in_approved_appointment,
	get_appointment_detail_for_nurse,
	get_nurse_review_options,
	get_pending_appointment_requests,
)
from app.services.visit_workflow_service import (
	create_walkin_or_emergency_visit,
	create_visit_from_checked_in_appointment,
	get_prioritized_visit_queue,
	get_patient_for_registration,
	get_triage_form_data,
	get_walkin_registration_options,
	register_walkin_patient,
	save_triage_form,
	search_existing_patients,
)

bp = Blueprint("nurse", __name__)


@bp.get("/nurse/appointments/review")
@login_required
@role_required("clinic_nurse")
def appointments_review():
	"""Show pending appointment requests for nurse review."""
	try:
		result = get_pending_appointment_requests()
	except mysql.connector.Error:
		flash("Database is unavailable. Please try again later.", "danger")
		result = {"appointments": []}

	return render_template(
		"nurse/appointments_review.html",
		page_title="Appointment Review",
		appointments=result["appointments"],
	)


@bp.get("/nurse/appointments/<int:appointment_id>/review")
@login_required
@role_required("clinic_nurse")
def appointment_review_detail(appointment_id: int):
	"""Open one appointment for nurse review."""
	try:
		result = get_appointment_detail_for_nurse(appointment_id)
		options = get_nurse_review_options()
	except mysql.connector.Error:
		flash("Database is unavailable. Please try again later.", "danger")
		return redirect(url_for("nurse.appointments_review"))

	if not result["ok"]:
		flash(result["message"], "warning")
		return redirect(url_for("nurse.appointments_review"))

	return render_template(
		"nurse/appointment_review_detail.html",
		page_title="Review Appointment",
		appointment=result["appointment"],
		physicians=options["physicians"],
	)


@bp.post("/nurse/appointments/<int:appointment_id>/review")
@login_required
@role_required("clinic_nurse")
def appointment_review_submit(appointment_id: int):
	"""Approve/adjust/decline one appointment request."""
	nurse_user_id = int(session["user_id"])
	decision = (request.form.get("decision") or "").strip().lower()
	ip_address = request.remote_addr or "127.0.0.1"

	if decision == "decline":
		new_status = "cancelled"
		physician_user_id = None
		scheduled_date = None
		scheduled_time = None
	else:
		new_status = "approved"
		physician_user_id = request.form.get("physician_user_id", type=int)
		scheduled_date = request.form.get("scheduled_date") or None
		scheduled_time = request.form.get("scheduled_time") or None

		if not physician_user_id or not scheduled_date or not scheduled_time:
			flash("Physician, date, and time are required when approving/adjusting.", "danger")
			return redirect(url_for("nurse.appointment_review_detail", appointment_id=appointment_id))

	try:
		result = approve_adjust_or_decline_appointment(
			appointment_id=appointment_id,
			nurse_user_id=nurse_user_id,
			new_status=new_status,
			physician_user_id=physician_user_id,
			scheduled_date=scheduled_date,
			scheduled_time=scheduled_time,
			ip_address=ip_address,
		)
	except mysql.connector.Error as exc:
		flash(str(exc), "danger")
		return redirect(url_for("nurse.appointment_review_detail", appointment_id=appointment_id))

	if not result["ok"]:
		flash(result["message"], "danger")
		return redirect(url_for("nurse.appointment_review_detail", appointment_id=appointment_id))

	try:
		log_audit_event(
			user_id=nurse_user_id,
			action_type="appointment_updated",
			entity_type="appointments",
			entity_id=appointment_id,
			description=f"Nurse {decision} appointment #{appointment_id}.",
			ip_address=ip_address,
		)
	except mysql.connector.Error:
		pass

	flash("Appointment updated successfully.", "success")
	return redirect(url_for("nurse.appointment_review_detail", appointment_id=appointment_id))


@bp.get("/nurse/appointments/<int:appointment_id>/check-in")
@login_required
@role_required("clinic_nurse")
def check_in_page(appointment_id: int):
	"""Render check-in confirmation page."""
	try:
		result = get_appointment_detail_for_nurse(appointment_id)
	except mysql.connector.Error:
		flash("Database is unavailable. Please try again later.", "danger")
		return redirect(url_for("nurse.appointments_review"))

	if not result["ok"]:
		flash(result["message"], "warning")
		return redirect(url_for("nurse.appointments_review"))

	return render_template(
		"nurse/check_in.html",
		page_title="Check In Appointment",
		appointment=result["appointment"],
		checked_in_success=False,
	)


@bp.post("/nurse/appointments/<int:appointment_id>/check-in")
@login_required
@role_required("clinic_nurse")
def check_in_submit(appointment_id: int):
	"""Check in an approved appointment."""
	nurse_user_id = int(session["user_id"])
	ip_address = request.remote_addr or "127.0.0.1"

	try:
		result = check_in_approved_appointment(
			appointment_id=appointment_id,
			nurse_user_id=nurse_user_id,
			ip_address=ip_address,
		)
	except mysql.connector.Error as exc:
		flash(str(exc), "danger")
		return redirect(url_for("nurse.check_in_page", appointment_id=appointment_id))

	if not result["ok"]:
		flash(result["message"], "danger")
		return redirect(url_for("nurse.check_in_page", appointment_id=appointment_id))

	try:
		log_audit_event(
			user_id=nurse_user_id,
			action_type="appointment_checked_in",
			entity_type="appointments",
			entity_id=appointment_id,
			description=f"Nurse checked in appointment #{appointment_id}.",
			ip_address=ip_address,
		)
	except mysql.connector.Error:
		pass

	try:
		detail = get_appointment_detail_for_nurse(appointment_id)
	except mysql.connector.Error:
		flash("Appointment checked in, but detail reload failed.", "warning")
		return redirect(url_for("nurse.appointments_review"))

	flash("Appointment checked in successfully.", "success")
	return render_template(
		"nurse/check_in.html",
		page_title="Check In Appointment",
		appointment=detail.get("appointment"),
		checked_in_success=True,
	)


@bp.post("/nurse/appointments/<int:appointment_id>/create-visit")
@login_required
@role_required("clinic_nurse")
def create_visit_submit(appointment_id: int):
	"""Create a linked visit for a checked-in appointment."""
	nurse_user_id = int(session["user_id"])
	ip_address = request.remote_addr or "127.0.0.1"

	try:
		result = create_visit_from_checked_in_appointment(
			appointment_id=appointment_id,
			created_by_user_id=nurse_user_id,
			ip_address=ip_address,
		)
	except mysql.connector.Error as exc:
		flash(str(exc), "danger")
		return redirect(url_for("nurse.check_in_page", appointment_id=appointment_id))

	if not result["ok"]:
		flash(result["message"], "danger")
		return redirect(url_for("nurse.check_in_page", appointment_id=appointment_id))

	try:
		log_audit_event(
			user_id=nurse_user_id,
			action_type="visit_created_from_appointment",
			entity_type="visits",
			entity_id=int(result["visit_id"]),
			description=f"Created visit #{result['visit_id']} from appointment #{appointment_id}.",
			ip_address=ip_address,
		)
	except mysql.connector.Error:
		pass

	flash(f"Visit created successfully (Visit #{result['visit_id']}).", "success")
	return redirect(url_for("nurse.visit_queue"))


@bp.get("/nurse/patients/search")
@login_required
@role_required("clinic_nurse")
def patient_search_page():
	"""Search existing patients before walk-in/emergency registration."""
	keyword = (request.args.get("q") or "").strip()
	patients = []

	if keyword:
		try:
			result = search_existing_patients(keyword)
		except mysql.connector.Error:
			flash("Database is unavailable. Please try again later.", "danger")
			result = {"patients": []}
		patients = result["patients"]

	return render_template(
		"nurse/patient_search.html",
		page_title="Patient Search",
		keyword=keyword,
		patients=patients,
	)


@bp.post("/nurse/patients/register")
@login_required
@role_required("clinic_nurse")
def patient_register_submit():
	"""Register basic patient profile for walk-in/emergency use."""
	patient_category = (request.form.get("patient_category") or "").strip()
	full_name = (request.form.get("full_name") or "").strip()
	institutional_email = (request.form.get("institutional_email") or "").strip()
	contact_number = (request.form.get("contact_number") or "").strip() or None

	try:
		result = register_walkin_patient(
			patient_category=patient_category,
			full_name=full_name,
			institutional_email=institutional_email,
			contact_number=contact_number,
		)
	except mysql.connector.Error as exc:
		flash(str(exc), "danger")
		return redirect(url_for("nurse.patient_search_page"))

	if not result["ok"]:
		flash(result["message"], "danger")
		return redirect(url_for("nurse.patient_search_page"))

	flash("Patient profile created. Continue to visit registration.", "success")
	return redirect(
		url_for(
			"nurse.walkin_emergency_register_page",
			patient_profile_id=result["patient_profile_id"],
		)
	)


@bp.get("/nurse/visits/walkin-emergency/register")
@login_required
@role_required("clinic_nurse")
def walkin_emergency_register_page():
	"""Render walk-in/emergency visit registration form."""
	patient_profile_id = request.args.get("patient_profile_id", type=int)

	try:
		options = get_walkin_registration_options()
		selected_patient = None
		if patient_profile_id:
			patient_lookup = get_patient_for_registration(patient_profile_id)
			selected_patient = patient_lookup["patient"]
	except mysql.connector.Error:
		flash("Database is unavailable. Please try again later.", "danger")
		return redirect(url_for("nurse.patient_search_page"))

	return render_template(
		"nurse/walkin_emergency_register.html",
		page_title="Walk-In / Emergency Registration",
		consultation_types=options["consultation_types"],
		triage_levels=options["triage_levels"],
		physicians=options["physicians"],
		selected_patient=selected_patient,
		patient_profile_id=patient_profile_id,
	)


@bp.post("/nurse/visits/walkin-emergency/register")
@login_required
@role_required("clinic_nurse")
def walkin_emergency_register_submit():
	"""Create walk-in/emergency visit from nurse form."""
	nurse_user_id = int(session["user_id"])
	ip_address = request.remote_addr or "127.0.0.1"

	patient_profile_id = request.form.get("patient_profile_id", type=int)
	physician_user_id = request.form.get("physician_user_id", type=int)
	consultation_type_id = request.form.get("consultation_type_id", type=int)
	triage_level_id = request.form.get("triage_level_id", type=int)
	arrival_time_raw = request.form.get("arrival_time")

	if not patient_profile_id or not physician_user_id or not consultation_type_id:
		flash("Patient, physician, and consultation type are required.", "danger")
		return redirect(url_for("nurse.walkin_emergency_register_page", patient_profile_id=patient_profile_id))

	arrival_time = None
	if arrival_time_raw:
		try:
			arrival_time = datetime.strptime(arrival_time_raw, "%Y-%m-%dT%H:%M")
		except ValueError:
			flash("Invalid arrival time format.", "danger")
			return redirect(url_for("nurse.walkin_emergency_register_page", patient_profile_id=patient_profile_id))

	try:
		result = create_walkin_or_emergency_visit(
			patient_profile_id=patient_profile_id,
			physician_user_id=physician_user_id,
			consultation_type_id=consultation_type_id,
			triage_level_id=triage_level_id,
			created_by_user_id=nurse_user_id,
			arrival_time=arrival_time,
			ip_address=ip_address,
		)
	except mysql.connector.Error as exc:
		flash(str(exc), "danger")
		return redirect(url_for("nurse.walkin_emergency_register_page", patient_profile_id=patient_profile_id))

	if not result["ok"]:
		flash(result["message"], "danger")
		return redirect(url_for("nurse.walkin_emergency_register_page", patient_profile_id=patient_profile_id))

	try:
		log_audit_event(
			user_id=nurse_user_id,
			action_type="visit_created_walkin_emergency",
			entity_type="visits",
			entity_id=int(result["visit_id"]),
			description=f"Created walk-in/emergency visit #{result['visit_id']}.",
			ip_address=ip_address,
		)
	except mysql.connector.Error:
		pass

	flash("Visit created. Continue with triage form.", "success")
	return redirect(url_for("nurse.triage_form_page", visit_id=result["visit_id"]))


@bp.get("/nurse/visits/<int:visit_id>/triage")
@login_required
@role_required("clinic_nurse")
def triage_form_page(visit_id: int):
	"""Render triage form for a visit."""
	try:
		result = get_triage_form_data(visit_id)
	except mysql.connector.Error:
		flash("Database is unavailable. Please try again later.", "danger")
		return redirect(url_for("nurse.visit_queue"))

	if not result["ok"]:
		flash(result["message"], "warning")
		return redirect(url_for("nurse.visit_queue"))

	return render_template(
		"nurse/triage_form.html",
		page_title="Triage Form",
		visit=result["visit"],
		triage=result["triage"],
	)


@bp.post("/nurse/visits/<int:visit_id>/triage")
@login_required
@role_required("clinic_nurse")
def triage_form_submit(visit_id: int):
	"""Save triage form values for a visit."""
	notified_flag = request.form.get("emergency_contact_notified")
	notified_at_raw = request.form.get("emergency_contact_notified_at")
	notified_at = None
	if notified_at_raw:
		try:
			notified_at = datetime.strptime(notified_at_raw, "%Y-%m-%dT%H:%M")
		except ValueError:
			flash("Invalid guardian notification date/time.", "danger")
			return redirect(url_for("nurse.triage_form_page", visit_id=visit_id))

	try:
		result = save_triage_form(
			visit_id=visit_id,
			bp=(request.form.get("bp") or "").strip() or None,
			heart_rate=request.form.get("heart_rate", type=int),
			respiratory_rate=request.form.get("respiratory_rate", type=int),
			temperature=request.form.get("temperature", type=float),
			oxygen_saturation=request.form.get("oxygen_saturation", type=int),
			weight=request.form.get("weight", type=float),
			initial_assessment=(request.form.get("initial_assessment") or "").strip() or None,
			immediate_action=(request.form.get("immediate_action") or "").strip() or None,
			referral_details=(request.form.get("referral_details") or "").strip() or None,
			emergency_contact_notified=True if notified_flag == "1" else False if notified_flag == "0" else None,
			emergency_contact_notified_at=notified_at,
			notes=(request.form.get("notes") or "").strip() or None,
		)
	except mysql.connector.Error as exc:
		flash(str(exc), "danger")
		return redirect(url_for("nurse.triage_form_page", visit_id=visit_id))

	if not result["ok"]:
		flash(result["message"], "danger")
		return redirect(url_for("nurse.triage_form_page", visit_id=visit_id))

	try:
		log_audit_event(
			user_id=int(session["user_id"]),
			action_type="triage_updated",
			entity_type="triage_records",
			entity_id=visit_id,
			description=f"Saved triage details for visit #{visit_id}.",
			ip_address=request.remote_addr or "127.0.0.1",
		)
	except mysql.connector.Error:
		pass

	flash("Triage saved successfully.", "success")
	return redirect(url_for("nurse.visit_queue"))


@bp.get("/nurse/queue")
@login_required
@role_required("clinic_nurse")
def queue_overview():
	"""Backward-compatible route for nurse queue page."""
	return redirect(url_for("nurse.visit_queue"))


@bp.get("/nurse/visits/queue")
@login_required
@role_required("clinic_nurse")
def visit_queue():
	"""Show prioritized queue (emergency before routine)."""
	try:
		result = get_prioritized_visit_queue()
	except mysql.connector.Error:
		flash("Database is unavailable. Please try again later.", "danger")
		result = {"queue": []}

	return render_template(
		"nurse/visit_queue.html",
		page_title="Visit Queue",
		queue=result["queue"],
	)

