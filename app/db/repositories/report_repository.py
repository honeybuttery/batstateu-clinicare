"""Reporting repository for clinic admin dashboards and de-identified reports."""

from __future__ import annotations

from typing import Any

from app.db.connection import get_db_cursor


REPORT_CATALOG = [
    {
        "key": "appointments_status_mix",
        "title": "Appointment Status Mix",
        "description": "Count of appointments by status.",
    },
    {
        "key": "visit_flow_daily_30d",
        "title": "Visit Flow (Last 30 Days)",
        "description": "Daily visit volume and completion trend.",
    },
    {
        "key": "consultations_daily_30d",
        "title": "Consultations per Day (Last 30 Days)",
        "description": "Daily consultation count for operational monitoring.",
    },
    {
        "key": "patient_service_records",
        "title": "Patient Service Records",
        "description": "Unified list of scheduled appointments and walk-in/emergency visits.",
    },
    {
        "key": "patients_with_completed_visits",
        "title": "Patients with Completed Visits",
        "description": "Patients who have at least one completed clinic visit.",
    },
]


def get_operations_summary() -> dict[str, int]:
    with get_db_cursor() as cur:
        cur.execute("SELECT COUNT(*) AS c FROM appointments")
        appointments_total = int((cur.fetchone() or {}).get("c", 0))

        cur.execute("SELECT COUNT(*) AS c FROM visits")
        visits_total = int((cur.fetchone() or {}).get("c", 0))

        cur.execute("SELECT COUNT(*) AS c FROM consultations")
        consultations_total = int((cur.fetchone() or {}).get("c", 0))

        cur.execute("SELECT COUNT(*) AS c FROM appointments WHERE status = 'pending'")
        appointments_pending = int((cur.fetchone() or {}).get("c", 0))

        cur.execute("SELECT COUNT(*) AS c FROM visits WHERE visit_status IN ('queued', 'in_progress')")
        visits_active_queue = int((cur.fetchone() or {}).get("c", 0))

    return {
        "appointments_total": appointments_total,
        "visits_total": visits_total,
        "consultations_total": consultations_total,
        "appointments_pending": appointments_pending,
        "visits_active_queue": visits_active_queue,
    }


def list_available_reports() -> list[dict[str, str]]:
    return REPORT_CATALOG


def get_deidentified_report(report_key: str) -> dict[str, Any] | None:
    with get_db_cursor() as cur:
        if report_key == "appointments_status_mix":
            cur.execute(
                """
                SELECT status, COUNT(*) AS total_count
                FROM appointments
                GROUP BY status
                ORDER BY total_count DESC
                """
            )
        elif report_key == "visit_flow_daily_30d":
            cur.execute(
                """
                SELECT
                    DATE(arrival_time) AS visit_date,
                    COUNT(*) AS total_visits,
                    SUM(CASE WHEN visit_status = 'completed' THEN 1 ELSE 0 END) AS completed_visits,
                    SUM(CASE WHEN visit_status IN ('queued', 'in_progress') THEN 1 ELSE 0 END) AS active_visits
                FROM visits
                WHERE arrival_time >= DATE_SUB(CURDATE(), INTERVAL 30 DAY)
                GROUP BY DATE(arrival_time)
                ORDER BY visit_date DESC
                """
            )
        elif report_key == "consultations_daily_30d":
            cur.execute(
                """
                SELECT
                    DATE(c.created_at) AS consultation_date,
                    COUNT(*) AS consultation_count
                FROM consultations c
                WHERE c.created_at >= DATE_SUB(CURDATE(), INTERVAL 30 DAY)
                GROUP BY DATE(c.created_at)
                ORDER BY consultation_date DESC
                """
            )
        elif report_key == "patient_service_records":
            cur.execute(
                """
                SELECT
                    pp.full_name AS patient_name,
                    a.scheduled_date AS service_date,
                    a.reason AS concern,
                    'Appointment' AS record_type
                FROM appointments a
                JOIN patient_profiles pp
                    ON pp.patient_profile_id = a.patient_profile_id

                UNION

                SELECT
                    pp.full_name AS patient_name,
                    DATE(v.arrival_time) AS service_date,
                    tr.initial_assessment AS concern,
                    'Walk-in/Emergency Visit' AS record_type
                FROM visits v
                JOIN patient_profiles pp
                    ON pp.patient_profile_id = v.patient_profile_id
                LEFT JOIN triage_records tr
                    ON tr.visit_id = v.visit_id
                WHERE v.source_appointment_id IS NULL
                ORDER BY service_date DESC
                """
            )
        elif report_key == "patients_with_completed_visits":
            cur.execute(
                """
                SELECT
                    pp.patient_profile_id,
                    pp.full_name,
                    pp.institutional_email
                FROM patient_profiles pp
                WHERE pp.patient_profile_id IN (
                    SELECT v.patient_profile_id
                    FROM visits v
                    WHERE v.visit_status = 'completed'
                )
                ORDER BY pp.full_name ASC
                """
            )
        else:
            return None

        rows = cur.fetchall()

    report_meta = next((r for r in REPORT_CATALOG if r["key"] == report_key), None)
    if not report_meta:
        return None

    columns = list(rows[0].keys()) if rows else []
    return {
        "key": report_key,
        "title": report_meta["title"],
        "description": report_meta["description"],
        "columns": columns,
        "rows": rows,
    }
