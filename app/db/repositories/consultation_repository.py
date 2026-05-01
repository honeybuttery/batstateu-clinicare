"""Consultation repository for physician workflow."""

from __future__ import annotations

from typing import Any

from app.db.connection import get_db_cursor


def get_consultation_by_visit_id(visit_id: int) -> dict[str, Any] | None:
    with get_db_cursor() as cur:
        cur.execute(
            """
            SELECT
                consultation_id,
                visit_id,
                history,
                physical_exam,
                assessment,
                `plan`,
                follow_up_instructions,
                created_by_physician_id,
                created_at,
                updated_at
            FROM consultations
            WHERE visit_id = %s
            LIMIT 1
            """,
            (visit_id,),
        )
        return cur.fetchone()


def upsert_consultation_for_visit(
    *,
    visit_id: int,
    created_by_physician_id: int,
    history: str | None,
    physical_exam: str | None,
    assessment: str | None,
    plan: str | None,
    follow_up_instructions: str | None,
) -> int:
    existing = get_consultation_by_visit_id(visit_id)

    with get_db_cursor() as cur:
        if existing:
            cur.execute(
                """
                UPDATE consultations
                SET
                    history = %s,
                    physical_exam = %s,
                    assessment = %s,
                    `plan` = %s,
                    follow_up_instructions = %s
                WHERE consultation_id = %s
                """,
                (
                    history,
                    physical_exam,
                    assessment,
                    plan,
                    follow_up_instructions,
                    existing["consultation_id"],
                ),
            )
            return int(existing["consultation_id"])

        cur.execute(
            """
            INSERT INTO consultations (
                visit_id,
                history,
                physical_exam,
                assessment,
                `plan`,
                follow_up_instructions,
                created_by_physician_id
            ) VALUES (%s, %s, %s, %s, %s, %s, %s)
            """,
            (
                visit_id,
                history,
                physical_exam,
                assessment,
                plan,
                follow_up_instructions,
                created_by_physician_id,
            ),
        )
        return int(cur.lastrowid)


def list_patient_consultation_history(patient_profile_id: int, limit: int = 30) -> list[dict[str, Any]]:
    with get_db_cursor() as cur:
        cur.execute(
            """
            SELECT
                c.consultation_id,
                c.visit_id,
                c.history,
                c.physical_exam,
                c.assessment,
                c.`plan`,
                c.follow_up_instructions,
                c.created_at,
                c.updated_at,
                v.arrival_time,
                v.visit_status,
                lct.display_name AS consultation_type_name,
                u.institutional_email AS physician_email
            FROM consultations c
            JOIN visits v ON v.visit_id = c.visit_id
            JOIN users u ON u.user_id = v.physician_user_id
            JOIN lookup_consultation_types lct ON lct.consultation_type_id = v.consultation_type_id
            WHERE v.patient_profile_id = %s
            ORDER BY v.arrival_time DESC
            LIMIT %s
            """,
            (patient_profile_id, limit),
        )
        return cur.fetchall()


def list_patient_medical_records(patient_profile_id: int, limit: int = 50) -> list[dict[str, Any]]:
    with get_db_cursor() as cur:
        cur.execute(
            """
            SELECT
                c.consultation_id,
                c.visit_id,
                c.history,
                c.physical_exam,
                c.assessment,
                c.`plan`,
                c.follow_up_instructions,
                c.created_at,
                v.arrival_time,
                v.visit_status,
                lct.display_name AS consultation_type_name,
                tl.display_name AS triage_level_name,
                tr.bp,
                tr.heart_rate,
                tr.respiratory_rate,
                tr.temperature,
                tr.oxygen_saturation,
                tr.weight,
                tr.initial_assessment,
                tr.immediate_action,
                tr.referral_details,
                tr.notes AS triage_notes
            FROM consultations c
            JOIN visits v ON v.visit_id = c.visit_id
            JOIN lookup_consultation_types lct ON lct.consultation_type_id = v.consultation_type_id
            LEFT JOIN lookup_triage_levels tl ON tl.triage_level_id = v.triage_level_id
            LEFT JOIN triage_records tr ON tr.visit_id = v.visit_id
            WHERE v.patient_profile_id = %s
            GROUP BY
                c.consultation_id,
                c.visit_id,
                c.history,
                c.physical_exam,
                c.assessment,
                c.`plan`,
                c.follow_up_instructions,
                c.created_at,
                v.arrival_time,
                v.visit_status,
                lct.display_name,
                tl.display_name,
                tr.bp,
                tr.heart_rate,
                tr.respiratory_rate,
                tr.temperature,
                tr.oxygen_saturation,
                tr.weight,
                tr.initial_assessment,
                tr.immediate_action,
                tr.referral_details,
                tr.notes
            ORDER BY v.arrival_time DESC
            LIMIT %s
            """,
            (patient_profile_id, limit),
        )
        return cur.fetchall()
