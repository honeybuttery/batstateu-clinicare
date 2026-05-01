"""Triage repository for nurse triage records."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from app.db.connection import get_db_cursor


def get_triage_record_by_visit_id(visit_id: int) -> dict[str, Any] | None:
    with get_db_cursor() as cur:
        cur.execute(
            """
            SELECT
                triage_id,
                visit_id,
                bp,
                heart_rate,
                respiratory_rate,
                temperature,
                oxygen_saturation,
                weight,
                initial_assessment,
                immediate_action,
                referral_details,
                emergency_contact_notified,
                emergency_contact_notified_at,
                notes
            FROM triage_records
            WHERE visit_id = %s
            LIMIT 1
            """,
            (visit_id,),
        )
        return cur.fetchone()


def upsert_triage_record(
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
) -> int:
    with get_db_cursor() as cur:
        cur.execute(
            """
            INSERT INTO triage_records (
                visit_id,
                bp,
                heart_rate,
                respiratory_rate,
                temperature,
                oxygen_saturation,
                weight,
                initial_assessment,
                immediate_action,
                referral_details,
                emergency_contact_notified,
                emergency_contact_notified_at,
                notes
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE
                bp = VALUES(bp),
                heart_rate = VALUES(heart_rate),
                respiratory_rate = VALUES(respiratory_rate),
                temperature = VALUES(temperature),
                oxygen_saturation = VALUES(oxygen_saturation),
                weight = VALUES(weight),
                initial_assessment = VALUES(initial_assessment),
                immediate_action = VALUES(immediate_action),
                referral_details = VALUES(referral_details),
                emergency_contact_notified = VALUES(emergency_contact_notified),
                emergency_contact_notified_at = VALUES(emergency_contact_notified_at),
                notes = VALUES(notes)
            """,
            (
                visit_id,
                bp,
                heart_rate,
                respiratory_rate,
                temperature,
                oxygen_saturation,
                weight,
                initial_assessment,
                immediate_action,
                referral_details,
                emergency_contact_notified,
                emergency_contact_notified_at,
                notes,
            ),
        )
        return int(cur.lastrowid or 0)
