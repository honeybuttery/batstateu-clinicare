"""Patient medical records service for patient-user self-view."""

from __future__ import annotations

from typing import Any

from app.db.repositories.consultation_repository import list_patient_medical_records
from app.db.repositories.patient_repository import get_patient_profile_by_user_id, update_patient_profile


def get_patient_medical_records_for_user(user_id: int) -> dict[str, Any]:
    patient = get_patient_profile_by_user_id(user_id)
    if not patient:
        return {
            "ok": False,
            "message": "Patient profile not found for this account.",
            "patient": None,
            "records": [],
        }

    records = list_patient_medical_records(patient["patient_profile_id"])
    return {
        "ok": True,
        "message": "",
        "patient": patient,
        "records": records,
    }


def update_patient_profile_for_user(
    user_id: int,
    *,
    full_name: str | None = None,
    contact_number: str | None = None,
    allergies: str | None = None,
    known_conditions: str | None = None,
    current_medications: str | None = None,
    student_course: str | None = None,
    student_year_level: int | None = None,
    faculty_staff_department: str | None = None,
) -> dict[str, Any]:
	"""Update patient profile for logged-in user."""
	patient = get_patient_profile_by_user_id(user_id)
	if not patient:
		return {"ok": False, "message": "Patient profile not found for this account."}
	
	success = update_patient_profile(
		patient_profile_id=patient["patient_profile_id"],
		full_name=full_name,
		contact_number=contact_number,
		allergies=allergies,
		known_conditions=known_conditions,
		current_medications=current_medications,
        student_course=student_course,
        student_year_level=student_year_level,
        faculty_staff_department=faculty_staff_department,
	)
	
	if not success:
		return {"ok": False, "message": "Failed to update profile."}
	
	return {"ok": True, "message": "Profile updated successfully."}
