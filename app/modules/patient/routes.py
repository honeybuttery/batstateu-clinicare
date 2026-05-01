"""Patient routes (starter appointment request flow)."""

from __future__ import annotations

import mysql.connector
from flask import Blueprint, flash, redirect, render_template, request, session, url_for

from app.auth.decorators import login_required, role_required
from app.services.audit_service import log_audit_event
from app.services.appointment_service import (
	create_appointment_request,
	get_appointment_detail_for_user,
	get_appointment_form_options,
	get_patient_appointments,
)
from app.services.patient_record_service import get_patient_medical_records_for_user, update_patient_profile_for_user

bp = Blueprint("patient", __name__)


@bp.get("/")
def home() -> str:
	"""Render starter home page."""
	return render_template("home/index.html", page_title="Home")


@bp.get("/patient/appointments")
@login_required
@role_required("patient_user")
def appointments_list():
	"""Show appointments of the logged-in patient only."""
	user_id = int(session["user_id"])
	try:
		result = get_patient_appointments(user_id)
	except mysql.connector.Error:
		flash("Database is unavailable. Please try again later.", "danger")
		return render_template("patient/appointments_list.html", page_title="My Appointments", appointments=[])

	if not result["ok"]:
		flash(result["message"], "warning")
		return render_template("patient/appointments_list.html", page_title="My Appointments", appointments=[])

	return render_template(
		"patient/appointments_list.html",
		page_title="My Appointments",
		appointments=result["appointments"],
	)


@bp.get("/patient/appointments/request")
@login_required
@role_required("patient_user")
def appointment_request_page():
	"""Render appointment request form."""
	user_id = int(session["user_id"])
	try:
		result = get_appointment_form_options(user_id)
	except mysql.connector.Error:
		flash("Database is unavailable. Please try again later.", "danger")
		return redirect(url_for("patient.appointments_list"))

	if not result["ok"]:
		flash(result["message"], "warning")
		return redirect(url_for("patient.appointments_list"))

	return render_template(
		"patient/appointment_request.html",
		page_title="Request Appointment",
		physicians=result["physicians"],
		consultation_types=result["consultation_types"],
	)


@bp.post("/patient/appointments/request")
@login_required
@role_required("patient_user")
def appointment_request_submit():
	"""Submit a new appointment request via stored procedure."""
	user_id = int(session["user_id"])
	physician_user_id = request.form.get("physician_user_id", type=int)
	consultation_type_id = request.form.get("consultation_type_id", type=int)
	scheduled_date = request.form.get("scheduled_date") or None
	scheduled_time = request.form.get("scheduled_time") or None
	reason = (request.form.get("reason") or "").strip() or None
	ip_address = request.remote_addr or "127.0.0.1"

	if not physician_user_id or not consultation_type_id:
		flash("Please select a physician and consultation type.", "danger")
		return redirect(url_for("patient.appointment_request_page"))

	try:
		result = create_appointment_request(
			user_id=user_id,
			physician_user_id=physician_user_id,
			consultation_type_id=consultation_type_id,
			scheduled_date=scheduled_date,
			scheduled_time=scheduled_time,
			reason=reason,
			ip_address=ip_address,
		)
	except mysql.connector.Error:
		flash("Database is unavailable. Please try again later.", "danger")
		return redirect(url_for("patient.appointment_request_page"))

	if not result["ok"]:
		flash(result["message"], "danger")
		return redirect(url_for("patient.appointment_request_page"))

	try:
		log_audit_event(
			user_id=user_id,
			action_type="appointment_requested",
			entity_type="appointments",
			entity_id=int(result["appointment_id"]),
			description=f"Patient requested appointment #{result['appointment_id']}.",
			ip_address=ip_address,
		)
	except mysql.connector.Error:
		# Do not block patient flow if audit write fails.
		pass

	flash("Appointment request submitted successfully.", "success")
	return redirect(url_for("patient.appointment_detail", appointment_id=result["appointment_id"]))


@bp.get("/patient/appointments/<int:appointment_id>")
@login_required
@role_required("patient_user")
def appointment_detail(appointment_id: int):
	"""View one appointment detail/status of logged-in patient."""
	user_id = int(session["user_id"])
	try:
		result = get_appointment_detail_for_user(user_id=user_id, appointment_id=appointment_id)
	except mysql.connector.Error:
		flash("Database is unavailable. Please try again later.", "danger")
		return redirect(url_for("patient.appointments_list"))

	if not result["ok"]:
		flash(result["message"], "warning")
		return redirect(url_for("patient.appointments_list"))

	return render_template(
		"patient/appointment_detail.html",
		page_title="Appointment Detail",
		appointment=result["appointment"],
	)


@bp.get("/patient/medical-records")
@login_required
@role_required("patient_user")
def medical_records_page():
	"""Show medical records for the logged-in patient only."""
	user_id = int(session["user_id"])
	try:
		result = get_patient_medical_records_for_user(user_id)
	except mysql.connector.Error:
		flash("Database is unavailable. Please try again later.", "danger")
		return render_template(
			"patient/medical_records.html",
			page_title="My Medical Records",
			patient=None,
			records=[],
		)

	if not result["ok"]:
		flash(result["message"], "warning")
		return render_template(
			"patient/medical_records.html",
			page_title="My Medical Records",
			patient=None,
			records=[],
		)

	return render_template(
		"patient/medical_records.html",
		page_title="My Medical Records",
		patient=result["patient"],
		records=result["records"],
	)


@bp.get("/patient/profile/edit")
@login_required
@role_required("patient_user")
def edit_profile_page():
	"""Show profile edit form for logged-in patient."""
	user_id = int(session["user_id"])
	try:
		result = get_patient_medical_records_for_user(user_id)
	except mysql.connector.Error:
		flash("Database is unavailable. Please try again later.", "danger")
		return redirect(url_for("patient.medical_records_page"))

	if not result["ok"]:
		flash(result["message"], "warning")
		return redirect(url_for("patient.medical_records_page"))

	return render_template(
		"patient/edit_profile.html",
		page_title="Edit Profile",
		patient=result["patient"],
	)


@bp.post("/patient/profile/edit")
@login_required
@role_required("patient_user")
def edit_profile_submit():
	"""Save profile updates for logged-in patient."""
	user_id = int(session["user_id"])
	full_name = (request.form.get("full_name") or "").strip() or None
	contact_number = (request.form.get("contact_number") or "").strip() or None
	allergies = (request.form.get("allergies") or "").strip() or None
	known_conditions = (request.form.get("known_conditions") or "").strip() or None
	current_medications = (request.form.get("current_medications") or "").strip() or None
	ip_address = request.remote_addr or "127.0.0.1"

	try:
		result = update_patient_profile_for_user(
			user_id,
			full_name=full_name,
			contact_number=contact_number,
			allergies=allergies,
			known_conditions=known_conditions,
			current_medications=current_medications,
		)
	except mysql.connector.Error:
		flash("Database is unavailable. Please try again later.", "danger")
		return redirect(url_for("patient.edit_profile_page"))

	if not result["ok"]:
		flash(result["message"], "danger")
		return redirect(url_for("patient.edit_profile_page"))

	try:
		log_audit_event(
			user_id=user_id,
			action_type="profile_updated",
			entity_type="patient_profiles",
			entity_id=None,
			description="Patient updated their profile information.",
			ip_address=ip_address,
		)
	except mysql.connector.Error:
		pass  # Don't block if audit fails

	flash("Profile updated successfully.", "success")
	return redirect(url_for("patient.medical_records_page"))
