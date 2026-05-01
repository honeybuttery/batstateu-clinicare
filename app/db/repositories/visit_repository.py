"""Visit repository for nurse and physician workflows."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from app.db.connection import get_db_cursor


def create_visit_from_checked_in_appointment_via_sp(
    *,
    appointment_id: int,
    created_by_user_id: int,
    arrival_time: datetime,
    ip_address: str,
) -> int | None:
    with get_db_cursor() as cur:
        cur.execute(
            """
            CALL sp_create_visit_from_checked_in_appointment(%s, %s, %s, %s)
            """,
            (appointment_id, created_by_user_id, arrival_time, ip_address),
        )

        row = cur.fetchone()
        if row and "visit_id" in row:
            return int(row["visit_id"])

    return None


def list_active_queue_overview() -> list[dict[str, Any]]:
    with get_db_cursor() as cur:
        cur.execute(
            """
            SELECT
                v.visit_id,
                v.source_appointment_id,
                v.arrival_time,
                v.visit_status,
                v.created_at,
                pp.patient_profile_id,
                pp.full_name AS patient_name,
                pp.institutional_email AS patient_email,
                physician.institutional_email AS physician_email,
                lct.display_name AS consultation_type_name
            FROM visits v
            JOIN patient_profiles pp ON pp.patient_profile_id = v.patient_profile_id
            JOIN users physician ON physician.user_id = v.physician_user_id
            JOIN lookup_consultation_types lct ON lct.consultation_type_id = v.consultation_type_id
            WHERE v.visit_status IN ('queued', 'in_progress')
            ORDER BY v.arrival_time ASC
            """
        )
        return cur.fetchall()


def list_walkin_emergency_physicians() -> list[dict[str, Any]]:
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


def get_walkin_emergency_consultation_types() -> list[dict[str, Any]]:
    with get_db_cursor() as cur:
        cur.execute(
            """
            SELECT consultation_type_id, code, display_name
            FROM lookup_consultation_types
            WHERE is_active = 1
              AND (
                LOWER(code) LIKE '%walk%'
                OR LOWER(code) LIKE '%emerg%'
                OR LOWER(display_name) LIKE '%walk%'
                OR LOWER(display_name) LIKE '%emerg%'
              )
            ORDER BY
                CASE WHEN LOWER(code) LIKE '%emerg%' OR LOWER(display_name) LIKE '%emerg%' THEN 0 ELSE 1 END,
                display_name ASC
            """
        )
        return cur.fetchall()


def get_triage_levels() -> list[dict[str, Any]]:
    with get_db_cursor() as cur:
        cur.execute(
            """
            SELECT triage_level_id, code, display_name
            FROM lookup_triage_levels
            WHERE is_active = 1
            ORDER BY triage_level_id ASC
            """
        )
        return cur.fetchall()


def create_walkin_or_emergency_visit_via_sp(
    *,
    patient_profile_id: int,
    physician_user_id: int,
    consultation_type_id: int,
    triage_level_id: int | None,
    created_by_user_id: int,
    arrival_time: datetime,
    ip_address: str,
) -> int | None:
    with get_db_cursor() as cur:
        cur.execute(
            """
            CALL sp_create_walkin_or_emergency_visit(%s, %s, %s, %s, %s, %s, %s)
            """,
            (
                patient_profile_id,
                physician_user_id,
                consultation_type_id,
                triage_level_id,
                created_by_user_id,
                arrival_time,
                ip_address,
            ),
        )

        row = cur.fetchone()
        if row and "visit_id" in row:
            return int(row["visit_id"])

    return None


def get_visit_detail_by_id(visit_id: int) -> dict[str, Any] | None:
    with get_db_cursor() as cur:
        cur.execute(
            """
            SELECT
                v.visit_id,
                v.patient_profile_id,
                v.physician_user_id,
                v.consultation_type_id,
                v.source_appointment_id,
                v.arrival_time,
                v.triage_level_id,
                v.visit_status,
                v.created_by_user_id,
                v.created_at,
                v.updated_at,
                pp.full_name AS patient_name,
                pp.institutional_email AS patient_email,
                physician.institutional_email AS physician_email,
                lct.code AS consultation_type_code,
                lct.display_name AS consultation_type_name,
                tl.display_name AS triage_level_name
            FROM visits v
            JOIN patient_profiles pp ON pp.patient_profile_id = v.patient_profile_id
            JOIN users physician ON physician.user_id = v.physician_user_id
            JOIN lookup_consultation_types lct ON lct.consultation_type_id = v.consultation_type_id
            LEFT JOIN lookup_triage_levels tl ON tl.triage_level_id = v.triage_level_id
            WHERE v.visit_id = %s
            LIMIT 1
            """,
            (visit_id,),
        )
        return cur.fetchone()


def list_prioritized_visit_queue() -> list[dict[str, Any]]:
    with get_db_cursor() as cur:
        cur.execute(
            """
            SELECT
                v.visit_id,
                v.arrival_time,
                v.visit_status,
                v.source_appointment_id,
                pp.full_name AS patient_name,
                pp.institutional_email AS patient_email,
                physician.institutional_email AS physician_email,
                lct.code AS consultation_type_code,
                lct.display_name AS consultation_type_name,
                tl.display_name AS triage_level_name
            FROM visits v
            JOIN patient_profiles pp ON pp.patient_profile_id = v.patient_profile_id
            JOIN users physician ON physician.user_id = v.physician_user_id
            JOIN lookup_consultation_types lct ON lct.consultation_type_id = v.consultation_type_id
            LEFT JOIN lookup_triage_levels tl ON tl.triage_level_id = v.triage_level_id
            WHERE v.visit_status IN ('queued', 'in_progress')
            ORDER BY
                CASE
                    WHEN LOWER(lct.code) LIKE '%emerg%' OR LOWER(lct.display_name) LIKE '%emerg%' THEN 0
                    ELSE 1
                END ASC,
                v.arrival_time ASC
            """
        )
        return cur.fetchall()


def list_visits_for_physician_queue(physician_user_id: int) -> list[dict[str, Any]]:
    with get_db_cursor() as cur:
        cur.execute(
            """
            SELECT
                v.visit_id,
                v.patient_profile_id,
                v.arrival_time,
                v.visit_status,
                pp.full_name AS patient_name,
                pp.institutional_email AS patient_email,
                lct.code AS consultation_type_code,
                lct.display_name AS consultation_type_name,
                tl.display_name AS triage_level_name,
                tr.triage_id,
                c.consultation_id
            FROM visits v
            JOIN patient_profiles pp ON pp.patient_profile_id = v.patient_profile_id
            JOIN lookup_consultation_types lct ON lct.consultation_type_id = v.consultation_type_id
            LEFT JOIN lookup_triage_levels tl ON tl.triage_level_id = v.triage_level_id
            LEFT JOIN triage_records tr ON tr.visit_id = v.visit_id
            LEFT JOIN consultations c ON c.visit_id = v.visit_id
            WHERE v.physician_user_id = %s
              AND v.visit_status IN ('queued', 'in_progress')
            ORDER BY
                CASE
                    WHEN LOWER(lct.code) LIKE '%emerg%' OR LOWER(lct.display_name) LIKE '%emerg%' THEN 0
                    ELSE 1
                END ASC,
                v.arrival_time ASC
            """,
            (physician_user_id,),
        )
        return cur.fetchall()


def get_visit_detail_for_physician(visit_id: int, physician_user_id: int) -> dict[str, Any] | None:
    with get_db_cursor() as cur:
        cur.execute(
            """
            SELECT
                v.visit_id,
                v.patient_profile_id,
                v.physician_user_id,
                v.consultation_type_id,
                v.source_appointment_id,
                v.arrival_time,
                v.triage_level_id,
                v.visit_status,
                v.created_at,
                v.updated_at,
                pp.full_name AS patient_name,
                pp.institutional_email AS patient_email,
                pp.patient_category,
                pp.contact_number,
                pp.allergies,
                pp.known_conditions,
                pp.current_medications,
                physician.institutional_email AS physician_email,
                lct.code AS consultation_type_code,
                lct.display_name AS consultation_type_name,
                tl.display_name AS triage_level_name,
                tr.triage_id,
                tr.bp,
                tr.heart_rate,
                tr.respiratory_rate,
                tr.temperature,
                tr.oxygen_saturation,
                tr.weight,
                tr.initial_assessment,
                tr.immediate_action,
                tr.referral_details,
                tr.emergency_contact_notified,
                tr.emergency_contact_notified_at,
                tr.notes AS triage_notes
            FROM visits v
            JOIN patient_profiles pp ON pp.patient_profile_id = v.patient_profile_id
            JOIN users physician ON physician.user_id = v.physician_user_id
            JOIN lookup_consultation_types lct ON lct.consultation_type_id = v.consultation_type_id
            LEFT JOIN lookup_triage_levels tl ON tl.triage_level_id = v.triage_level_id
            LEFT JOIN triage_records tr ON tr.visit_id = v.visit_id
            WHERE v.visit_id = %s
              AND v.physician_user_id = %s
            LIMIT 1
            """,
            (visit_id, physician_user_id),
        )
        return cur.fetchone()


def physician_has_visit_with_patient(physician_user_id: int, patient_profile_id: int) -> bool:
    with get_db_cursor() as cur:
        cur.execute(
            """
            SELECT 1
            FROM visits
            WHERE physician_user_id = %s
              AND patient_profile_id = %s
            LIMIT 1
            """,
            (physician_user_id, patient_profile_id),
        )
        return cur.fetchone() is not None
