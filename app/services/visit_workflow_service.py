"""Visit workflow service for nurse queue and triage workflows."""

from __future__ import annotations

from datetime import datetime, UTC
from typing import Any

from app.db.repositories.consultation_repository import (
	get_consultation_by_visit_id,
	list_patient_consultation_history,
	upsert_consultation_for_visit,
)
from app.db.repositories.patient_repository import (
	create_patient_profile_for_walkin,
	get_patient_profile_by_id,
	search_patient_profiles,
)
from app.db.repositories.triage_repository import (
	get_triage_record_by_visit_id,
	upsert_triage_record,
)
from app.db.repositories.visit_repository import (
	create_visit_from_checked_in_appointment_via_sp,
	create_walkin_or_emergency_visit_via_sp,
	get_triage_levels,
	get_visit_detail_by_id,
	get_walkin_emergency_consultation_types,
	get_visit_detail_for_physician,
	list_prioritized_visit_queue,
	list_visits_for_physician_queue,
	list_walkin_emergency_physicians,
	list_active_queue_overview,
	physician_has_visit_with_patient,
)


def create_visit_from_checked_in_appointment(
	*,
	appointment_id: int,
	created_by_user_id: int,
	ip_address: str,
	arrival_time: datetime | None = None,
) -> dict[str, Any]:
	if arrival_time is None:
		arrival_time = datetime.now(UTC).replace(tzinfo=None)

	visit_id = create_visit_from_checked_in_appointment_via_sp(
		appointment_id=appointment_id,
		created_by_user_id=created_by_user_id,
		arrival_time=arrival_time,
		ip_address=ip_address,
	)

	if not visit_id:
		return {"ok": False, "message": "Failed to create visit.", "visit_id": None}

	return {"ok": True, "message": "Visit created.", "visit_id": visit_id}


def get_queue_overview() -> dict[str, Any]:
	queue = list_active_queue_overview()
	return {"ok": True, "message": "", "queue": queue}


def search_existing_patients(keyword: str) -> dict[str, Any]:
	keyword = keyword.strip()
	if not keyword:
		return {"ok": True, "message": "", "patients": []}

	patients = search_patient_profiles(keyword)
	return {"ok": True, "message": "", "patients": patients}


def register_walkin_patient(
	*,
	patient_category: str,
	full_name: str,
	institutional_email: str,
	contact_number: str | None,
	student_course: str | None = None,
	student_year_level: int | None = None,
	faculty_staff_department: str | None = None,
) -> dict[str, Any]:
	if patient_category not in {"student", "faculty", "staff"}:
		return {"ok": False, "message": "Invalid patient category.", "patient_profile_id": None}

	if not full_name.strip() or not institutional_email.strip():
		return {"ok": False, "message": "Full name and email are required.", "patient_profile_id": None}

	patient_profile_id = create_patient_profile_for_walkin(
		patient_category=patient_category,
		full_name=full_name.strip(),
		institutional_email=institutional_email.strip().lower(),
		contact_number=(contact_number or "").strip() or None,
		student_course=(student_course or "").strip() or None,
		student_year_level=student_year_level,
		faculty_staff_department=(faculty_staff_department or "").strip() or None,
	)

	if not patient_profile_id:
		return {"ok": False, "message": "Failed to register patient.", "patient_profile_id": None}

	return {"ok": True, "message": "Patient registered.", "patient_profile_id": patient_profile_id}


def get_walkin_registration_options() -> dict[str, Any]:
	return {
		"ok": True,
		"message": "",
		"consultation_types": get_walkin_emergency_consultation_types(),
		"triage_levels": get_triage_levels(),
		"physicians": list_walkin_emergency_physicians(),
	}


def get_patient_for_registration(patient_profile_id: int) -> dict[str, Any]:
	patient = get_patient_profile_by_id(patient_profile_id)
	if not patient:
		return {"ok": False, "message": "Patient profile not found.", "patient": None}

	return {"ok": True, "message": "", "patient": patient}


def create_walkin_or_emergency_visit(
	*,
	patient_profile_id: int,
	physician_user_id: int,
	consultation_type_id: int,
	triage_level_id: int | None,
	created_by_user_id: int,
	arrival_time: datetime | None,
	ip_address: str,
) -> dict[str, Any]:
	patient = get_patient_profile_by_id(patient_profile_id)
	if not patient:
		return {"ok": False, "message": "Patient profile not found.", "visit_id": None}

	if arrival_time is None:
		arrival_time = datetime.now(UTC).replace(tzinfo=None)

	visit_id = create_walkin_or_emergency_visit_via_sp(
		patient_profile_id=patient_profile_id,
		physician_user_id=physician_user_id,
		consultation_type_id=consultation_type_id,
		triage_level_id=triage_level_id,
		created_by_user_id=created_by_user_id,
		arrival_time=arrival_time,
		ip_address=ip_address,
	)

	if not visit_id:
		return {"ok": False, "message": "Failed to create visit.", "visit_id": None}

	return {"ok": True, "message": "Visit created.", "visit_id": visit_id}


def get_triage_form_data(visit_id: int) -> dict[str, Any]:
	visit = get_visit_detail_by_id(visit_id)
	if not visit:
		return {"ok": False, "message": "Visit not found.", "visit": None, "triage": None}

	triage = get_triage_record_by_visit_id(visit_id)
	return {"ok": True, "message": "", "visit": visit, "triage": triage}


def save_triage_form(
	*,
	visit_id: int,
	bp: str | None,
	heart_rate: int | None,
	respiratory_rate: int | None,
	temperature: float | None,
	oxygen_saturation: int | None,
	weight: float | None,
	initial_assessment: str | None,
	immediate_action: str | None,
	referral_details: str | None,
	emergency_contact_notified: bool | None,
	emergency_contact_notified_at: datetime | None,
	notes: str | None,
) -> dict[str, Any]:
	visit = get_visit_detail_by_id(visit_id)
	if not visit:
		return {"ok": False, "message": "Visit not found."}

	upsert_triage_record(
		visit_id=visit_id,
		bp=bp,
		heart_rate=heart_rate,
		respiratory_rate=respiratory_rate,
		temperature=temperature,
		oxygen_saturation=oxygen_saturation,
		weight=weight,
		initial_assessment=initial_assessment,
		immediate_action=immediate_action,
		referral_details=referral_details,
		emergency_contact_notified=emergency_contact_notified,
		emergency_contact_notified_at=emergency_contact_notified_at,
		notes=notes,
	)

	return {"ok": True, "message": "Triage saved."}


def get_prioritized_visit_queue() -> dict[str, Any]:
	queue = list_prioritized_visit_queue()
	return {"ok": True, "message": "", "queue": queue}


def get_physician_queue(physician_user_id: int) -> dict[str, Any]:
	queue = list_visits_for_physician_queue(physician_user_id)
	return {"ok": True, "message": "", "queue": queue}


def get_physician_visit_detail(physician_user_id: int, visit_id: int) -> dict[str, Any]:
	visit = get_visit_detail_for_physician(visit_id=visit_id, physician_user_id=physician_user_id)
	if not visit:
		return {
			"ok": False,
			"message": "Visit not found or not assigned to you.",
			"visit": None,
			"consultation": None,
		}

	consultation = get_consultation_by_visit_id(visit_id)

	return {
		"ok": True,
		"message": "",
		"visit": visit,
		"consultation": consultation,
	}


def save_consultation(
	*,
	physician_user_id: int,
	visit_id: int,
	history: str | None,
	physical_exam: str | None,
	assessment: str | None,
	plan: str | None,
	follow_up_instructions: str | None,
) -> dict[str, Any]:
	visit = get_visit_detail_for_physician(visit_id=visit_id, physician_user_id=physician_user_id)
	if not visit:
		return {"ok": False, "message": "Visit not found or not assigned to you.", "consultation_id": None}

	consultation_id = upsert_consultation_for_visit(
		visit_id=visit_id,
		created_by_physician_id=physician_user_id,
		history=history,
		physical_exam=physical_exam,
		assessment=assessment,
		plan=plan,
		follow_up_instructions=follow_up_instructions,
	)

	return {
		"ok": True,
		"message": "Consultation saved.",
		"consultation_id": consultation_id,
	}


def get_patient_clinical_history(physician_user_id: int, patient_profile_id: int) -> dict[str, Any]:
	if not physician_has_visit_with_patient(physician_user_id, patient_profile_id):
		return {"ok": False, "message": "Patient history is not available for your account.", "patient": None, "history": []}

	patient = get_patient_profile_by_id(patient_profile_id)
	if not patient:
		return {"ok": False, "message": "Patient not found.", "patient": None, "history": []}

	history = list_patient_consultation_history(patient_profile_id)
	return {"ok": True, "message": "", "patient": patient, "history": history}
