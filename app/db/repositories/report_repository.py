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
