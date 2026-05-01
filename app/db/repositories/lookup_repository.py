"""Lookup repository for system admin management."""

from __future__ import annotations

from typing import Any

from app.db.connection import get_db_cursor


LOOKUP_TABLES = {
    "triage": ("lookup_triage_levels", "triage_level_id"),
    "consultation": ("lookup_consultation_types", "consultation_type_id"),
}


def _resolve_lookup(lookup_type: str) -> tuple[str, str]:
    if lookup_type not in LOOKUP_TABLES:
        raise ValueError("Invalid lookup type.")
    return LOOKUP_TABLES[lookup_type]


def list_lookup_values(lookup_type: str) -> list[dict[str, Any]]:
    table, id_col = _resolve_lookup(lookup_type)
    with get_db_cursor() as cur:
        cur.execute(
            f"""
            SELECT {id_col} AS lookup_id, code, display_name, is_active
            FROM {table}
            ORDER BY display_name ASC
            """
        )
        return cur.fetchall()


def get_lookup_value(lookup_type: str, lookup_id: int) -> dict[str, Any] | None:
    table, id_col = _resolve_lookup(lookup_type)
    with get_db_cursor() as cur:
        cur.execute(
            f"""
            SELECT {id_col} AS lookup_id, code, display_name, is_active
            FROM {table}
            WHERE {id_col} = %s
            LIMIT 1
            """,
            (lookup_id,),
        )
        return cur.fetchone()


def create_lookup_value(
    *,
    lookup_type: str,
    code: str,
    display_name: str,
    is_active: bool,
) -> int:
    table, id_col = _resolve_lookup(lookup_type)
    with get_db_cursor() as cur:
        cur.execute(
            f"""
            INSERT INTO {table} (code, display_name, is_active)
            VALUES (%s, %s, %s)
            """,
            (code, display_name, 1 if is_active else 0),
        )
        return int(cur.lastrowid)


def update_lookup_value(
    *,
    lookup_type: str,
    lookup_id: int,
    code: str,
    display_name: str,
    is_active: bool,
) -> bool:
    table, id_col = _resolve_lookup(lookup_type)
    with get_db_cursor() as cur:
        cur.execute(
            f"""
            UPDATE {table}
            SET code = %s,
                display_name = %s,
                is_active = %s
            WHERE {id_col} = %s
            """,
            (code, display_name, 1 if is_active else 0, lookup_id),
        )
        return cur.rowcount > 0
