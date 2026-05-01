"""Appointment repository for patient request flow."""

from __future__ import annotations

from typing import Any

from app.db.connection import get_db_cursor


def find_patient_profile_by_user_id(user_id: int) -> dict[str, Any] | None:
    with get_db_cursor() as cur:
        cur.execute(
            """
            SELECT patient_profile_id, user_id, full_name, institutional_email
            FROM patient_profiles
            WHERE user_id = %s
            LIMIT 1
            """,
            (user_id,),
        )
        return cur.fetchone()


def create_patient_profile_for_logged_in_user(user_id: int) -> dict[str, Any] | None:
	"""Auto-create patient profile for logged-in user on first appointment request."""
	with get_db_cursor() as cur:
		# Get user's full_name and institutional_email
		cur.execute(
			"""
			SELECT full_name, institutional_email FROM users WHERE user_id = %s LIMIT 1
			""",
			(user_id,),
		)
		user = cur.fetchone()
		if not user:
			return None
		
		full_name = user["full_name"] or user["institutional_email"]
		institutional_email = user["institutional_email"]
		
		# Create patient profile with minimal info (rest can be filled by admin/user later)
		cur.execute(
			"""
			INSERT INTO patient_profiles (
				user_id,
				patient_category,
				full_name,
				institutional_email,
				contact_number
			) VALUES (%s, %s, %s, %s, NULL)
			""",
			(user_id, "student", full_name, institutional_email),
		)
		
		patient_profile_id = int(cur.lastrowid)
		
		# Return the created profile
		cur.execute(
			"""
			SELECT patient_profile_id, user_id, full_name, institutional_email
			FROM patient_profiles
			WHERE patient_profile_id = %s
			LIMIT 1
			""",
			(patient_profile_id,),
		)
		return cur.fetchone()


def get_physicians() -> list[dict[str, Any]]:
    with get_db_cursor() as cur:
        cur.execute(
            """
            SELECT u.user_id, u.institutional_email
            FROM users u
            JOIN roles r ON r.role_id = u.role_id
            WHERE r.role_name = 'physician'
              AND u.account_status = 'active'
            ORDER BY u.institutional_email ASC
            """
        )
        return cur.fetchall()


def get_consultation_types() -> list[dict[str, Any]]:
    with get_db_cursor() as cur:
        cur.execute(
            """
            SELECT consultation_type_id, code, display_name
            FROM lookup_consultation_types
            WHERE is_active = 1
            ORDER BY display_name ASC
            """
        )
        return cur.fetchall()


def list_appointments_by_patient(patient_profile_id: int) -> list[dict[str, Any]]:
    with get_db_cursor() as cur:
        cur.execute(
            """
            SELECT
                a.appointment_id,
                a.scheduled_date,
                a.scheduled_time,
                a.reason,
                a.status,
                a.created_at,
                a.updated_at,
                a.physician_user_id,
                u.institutional_email AS physician_email,
                a.consultation_type_id,
                lct.display_name AS consultation_type_name
            FROM appointments a
            JOIN users u ON u.user_id = a.physician_user_id
            JOIN lookup_consultation_types lct ON lct.consultation_type_id = a.consultation_type_id
            WHERE a.patient_profile_id = %s
            ORDER BY a.created_at DESC
            """,
            (patient_profile_id,),
        )
        return cur.fetchall()


def get_appointment_detail_by_patient(patient_profile_id: int, appointment_id: int) -> dict[str, Any] | None:
    with get_db_cursor() as cur:
        cur.execute(
            """
            SELECT
                a.appointment_id,
                a.patient_profile_id,
                a.physician_user_id,
                a.requested_by_user_id,
                a.scheduled_date,
                a.scheduled_time,
                a.reason,
                a.status,
                a.created_at,
                a.updated_at,
                a.approved_by_user_id,
                a.consultation_type_id,
                physician.institutional_email AS physician_email,
                requester.institutional_email AS requested_by_email,
                approver.institutional_email AS approved_by_email,
                lct.display_name AS consultation_type_name
            FROM appointments a
            JOIN users physician ON physician.user_id = a.physician_user_id
            JOIN users requester ON requester.user_id = a.requested_by_user_id
            LEFT JOIN users approver ON approver.user_id = a.approved_by_user_id
            JOIN lookup_consultation_types lct ON lct.consultation_type_id = a.consultation_type_id
            WHERE a.patient_profile_id = %s AND a.appointment_id = %s
            LIMIT 1
            """,
            (patient_profile_id, appointment_id),
        )
        return cur.fetchone()


def create_appointment_request_via_sp(
    *,
    patient_profile_id: int,
    physician_user_id: int,
    requested_by_user_id: int,
    consultation_type_id: int,
    scheduled_date: str | None,
    scheduled_time: str | None,
    reason: str | None,
    ip_address: str,
) -> int | None:
    """Create appointment via stored procedure and return appointment_id."""
    with get_db_cursor() as cur:
        cur.execute(
            """
            CALL sp_create_appointment_request(%s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                patient_profile_id,
                physician_user_id,
                requested_by_user_id,
                consultation_type_id,
                scheduled_date,
                scheduled_time,
                reason,
                ip_address,
            ),
        )

        row = cur.fetchone()
        if row and "appointment_id" in row:
            return int(row["appointment_id"])

    return None


def list_pending_appointments_for_nurse_review() -> list[dict[str, Any]]:
    with get_db_cursor() as cur:
        cur.execute(
            """
            SELECT
                a.appointment_id,
                a.status,
                a.scheduled_date,
                a.scheduled_time,
                a.reason,
                a.created_at,
                pp.patient_profile_id,
                pp.full_name AS patient_name,
                pp.institutional_email AS patient_email,
                physician.institutional_email AS physician_email,
                requester.institutional_email AS requested_by_email,
                lct.display_name AS consultation_type_name
            FROM appointments a
            JOIN patient_profiles pp ON pp.patient_profile_id = a.patient_profile_id
            JOIN users physician ON physician.user_id = a.physician_user_id
            JOIN users requester ON requester.user_id = a.requested_by_user_id
            JOIN lookup_consultation_types lct ON lct.consultation_type_id = a.consultation_type_id
            WHERE a.status = 'pending'
            ORDER BY a.created_at ASC
            """
        )
        return cur.fetchall()


def get_appointment_detail_for_nurse_by_id(appointment_id: int) -> dict[str, Any] | None:
    with get_db_cursor() as cur:
        cur.execute(
            """
            SELECT
                a.appointment_id,
                a.patient_profile_id,
                a.physician_user_id,
                a.requested_by_user_id,
                a.scheduled_date,
                a.scheduled_time,
                a.reason,
                a.status,
                a.created_at,
                a.updated_at,
                a.approved_by_user_id,
                a.consultation_type_id,
                pp.full_name AS patient_name,
                pp.institutional_email AS patient_email,
                physician.institutional_email AS physician_email,
                requester.institutional_email AS requested_by_email,
                approver.institutional_email AS approved_by_email,
                lct.display_name AS consultation_type_name,
                v.visit_id AS linked_visit_id,
                v.visit_status
            FROM appointments a
            JOIN patient_profiles pp ON pp.patient_profile_id = a.patient_profile_id
            JOIN users physician ON physician.user_id = a.physician_user_id
            JOIN users requester ON requester.user_id = a.requested_by_user_id
            LEFT JOIN users approver ON approver.user_id = a.approved_by_user_id
            JOIN lookup_consultation_types lct ON lct.consultation_type_id = a.consultation_type_id
            LEFT JOIN visits v ON v.source_appointment_id = a.appointment_id
            WHERE a.appointment_id = %s
            LIMIT 1
            """,
            (appointment_id,),
        )
        return cur.fetchone()


def approve_or_adjust_appointment_via_sp(
    *,
    appointment_id: int,
    approved_by_user_id: int,
    new_physician_user_id: int | None,
    new_scheduled_date: str | None,
    new_scheduled_time: str | None,
    new_status: str,
    ip_address: str,
) -> int | None:
    with get_db_cursor() as cur:
        cur.execute(
            """
            CALL sp_approve_or_adjust_appointment(%s, %s, %s, %s, %s, %s, %s)
            """,
            (
                appointment_id,
                approved_by_user_id,
                new_physician_user_id,
                new_scheduled_date,
                new_scheduled_time,
                new_status,
                ip_address,
            ),
        )

        row = cur.fetchone()
        if row and "appointment_id" in row:
            return int(row["appointment_id"])

    return None


def check_in_appointment_via_sp(
    *,
    appointment_id: int,
    checked_in_by_user_id: int,
    ip_address: str,
) -> int | None:
    with get_db_cursor() as cur:
        cur.execute(
            """
            CALL sp_check_in_appointment(%s, %s, %s)
            """,
            (appointment_id, checked_in_by_user_id, ip_address),
        )

        row = cur.fetchone()
        if row and "appointment_id" in row:
            return int(row["appointment_id"])

    return None
