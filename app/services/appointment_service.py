"""Appointment service for patient and nurse workflows."""

from __future__ import annotations

from typing import Any

from app.db.repositories.appointment_repository import (
	approve_or_adjust_appointment_via_sp,
	check_in_appointment_via_sp,
	get_appointment_detail_for_nurse_by_id,
	create_appointment_request_via_sp,
	find_patient_profile_by_user_id,
	create_patient_profile_for_logged_in_user,
	get_appointment_detail_by_patient,
	get_consultation_types,
	get_physicians,
	list_pending_appointments_for_nurse_review,
	list_appointments_by_patient,
)


def get_patient_appointments(user_id: int) -> dict[str, Any]:
	patient_profile = find_patient_profile_by_user_id(user_id)
	
	# Auto-create patient profile if it doesn't exist
	if not patient_profile:
		patient_profile = create_patient_profile_for_logged_in_user(user_id)
	
	if not patient_profile:
		return {"ok": False, "message": "Unable to retrieve patient profile.", "appointments": []}

	appointments = list_appointments_by_patient(patient_profile["patient_profile_id"])
	return {"ok": True, "message": "", "appointments": appointments}


def get_appointment_form_options(user_id: int) -> dict[str, Any]:
	patient_profile = find_patient_profile_by_user_id(user_id)
	
	# Auto-create patient profile if it doesn't exist (optional - for consistency)
	if not patient_profile:
		patient_profile = create_patient_profile_for_logged_in_user(user_id)
		# If still fails, just show the form options anyway (form can still work)
		if not patient_profile:
			pass  # Continue to show form options

	return {
		"ok": True,
		"message": "",
		"physicians": get_physicians(),
		"consultation_types": get_consultation_types(),
	}


def create_appointment_request(
	*,
	user_id: int,
	physician_user_id: int,
	consultation_type_id: int,
	scheduled_date: str | None,
	scheduled_time: str | None,
	reason: str | None,
	ip_address: str,
) -> dict[str, Any]:
	patient_profile = find_patient_profile_by_user_id(user_id)
	
	# Auto-create patient profile if it doesn't exist
	if not patient_profile:
		patient_profile = create_patient_profile_for_logged_in_user(user_id)
		if not patient_profile:
			return {"ok": False, "message": "Failed to create patient profile.", "appointment_id": None}

	appointment_id = create_appointment_request_via_sp(
		patient_profile_id=patient_profile["patient_profile_id"],
		physician_user_id=physician_user_id,
		requested_by_user_id=user_id,
		consultation_type_id=consultation_type_id,
		scheduled_date=scheduled_date,
		scheduled_time=scheduled_time,
		reason=reason,
		ip_address=ip_address,
	)

	if not appointment_id:
		return {"ok": False, "message": "Failed to create appointment request.", "appointment_id": None}

	return {"ok": True, "message": "Appointment request created.", "appointment_id": appointment_id}


def get_appointment_detail_for_user(user_id: int, appointment_id: int) -> dict[str, Any]:
	patient_profile = find_patient_profile_by_user_id(user_id)
	if not patient_profile:
		return {"ok": False, "message": "Patient profile not found for this account.", "appointment": None}

	appointment = get_appointment_detail_by_patient(
		patient_profile_id=patient_profile["patient_profile_id"],
		appointment_id=appointment_id,
	)

	if not appointment:
		return {"ok": False, "message": "Appointment not found.", "appointment": None}

	return {"ok": True, "message": "", "appointment": appointment}


def get_pending_appointment_requests() -> dict[str, Any]:
	appointments = list_pending_appointments_for_nurse_review()
	return {"ok": True, "message": "", "appointments": appointments}


def get_nurse_review_options() -> dict[str, Any]:
	return {
		"ok": True,
		"message": "",
		"physicians": get_physicians(),
	}


def get_appointment_detail_for_nurse(appointment_id: int) -> dict[str, Any]:
	appointment = get_appointment_detail_for_nurse_by_id(appointment_id)
	if not appointment:
		return {"ok": False, "message": "Appointment not found.", "appointment": None}

	return {"ok": True, "message": "", "appointment": appointment}


def approve_adjust_or_decline_appointment(
	*,
	appointment_id: int,
	nurse_user_id: int,
	new_status: str,
	physician_user_id: int | None,
	scheduled_date: str | None,
	scheduled_time: str | None,
	ip_address: str,
) -> dict[str, Any]:
	if new_status not in {"approved", "cancelled"}:
		return {"ok": False, "message": "Invalid decision.", "appointment_id": None}

	updated_id = approve_or_adjust_appointment_via_sp(
		appointment_id=appointment_id,
		approved_by_user_id=nurse_user_id,
		new_physician_user_id=physician_user_id,
		new_scheduled_date=scheduled_date,
		new_scheduled_time=scheduled_time,
		new_status=new_status,
		ip_address=ip_address,
	)

	if not updated_id:
		return {"ok": False, "message": "Failed to update appointment.", "appointment_id": None}

	return {"ok": True, "message": "Appointment updated.", "appointment_id": updated_id}


def check_in_approved_appointment(
	*,
	appointment_id: int,
	nurse_user_id: int,
	ip_address: str,
) -> dict[str, Any]:
	updated_id = check_in_appointment_via_sp(
		appointment_id=appointment_id,
		checked_in_by_user_id=nurse_user_id,
		ip_address=ip_address,
	)

	if not updated_id:
		return {"ok": False, "message": "Failed to check in appointment.", "appointment_id": None}

	return {"ok": True, "message": "Appointment checked in.", "appointment_id": updated_id}
