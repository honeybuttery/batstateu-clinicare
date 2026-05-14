"""Audit repository for clinic and system admin views."""

from __future__ import annotations

from typing import Any

from app.db.connection import get_db_cursor


def list_audit_logs(
    *,
    limit: int = 200,
    action: str | None = None,
    action_like: str | None = None,
    entity: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
    user_id: int | None = None,
) -> list[dict[str, Any]]:
    """List audit logs with optional filters."""
    sql = [
        "SELECT",
        "    al.audit_log_id,",
        "    al.user_id,",
        "    u.institutional_email,",
        "    al.action_type,",
        "    al.entity_type,",
        "    al.entity_id,",
        "    al.description,",
        "    al.performed_at,",
        "    al.ip_address",
        "FROM audit_logs al",
        "JOIN users u ON u.user_id = al.user_id",
    ]

    params: list = []
    where: list[str] = []

    if action:
        where.append("al.action_type = %s")
        params.append(action)

    if action_like:
        where.append("al.action_type LIKE %s")
        params.append(action_like)

    if entity:
        where.append("al.entity_type = %s")
        params.append(entity)

    if user_id is not None:
        where.append("al.user_id = %s")
        params.append(user_id)

    if date_from:
        where.append("al.performed_at >= %s")
        params.append(date_from)

    if date_to:
        where.append("al.performed_at <= %s")
        params.append(date_to)

    if where:
        sql.append("WHERE " + " AND ".join(where))

    sql.append("ORDER BY al.performed_at DESC")
    sql.append("LIMIT %s")
    params.append(limit)

    with get_db_cursor() as cur:
        cur.execute("\n".join(sql), tuple(params))
        return cur.fetchall()


def list_audit_logs_deidentified(
    *,
    limit: int = 200,
    action: str | None = None,
    action_like: str | None = None,
    entity: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
) -> list[dict[str, Any]]:
    sql = [
        "SELECT",
        "    al.audit_log_id,",
        "    al.action_type,",
        "    al.entity_type,",
        "    al.entity_id,",
        "    al.description,",
        "    al.performed_at",
        "FROM audit_logs al",
    ]

    params: list = []
    where: list[str] = []

    if action:
        where.append("al.action_type = %s")
        params.append(action)

    if action_like:
        where.append("al.action_type LIKE %s")
        params.append(action_like)

    if entity:
        where.append("al.entity_type = %s")
        params.append(entity)

    if date_from:
        where.append("al.performed_at >= %s")
        params.append(date_from)

    if date_to:
        where.append("al.performed_at <= %s")
        params.append(date_to)

    if where:
        sql.append("WHERE " + " AND ".join(where))

    sql.append("ORDER BY al.performed_at DESC")
    sql.append("LIMIT %s")
    params.append(limit)

    with get_db_cursor() as cur:
        cur.execute("\n".join(sql), tuple(params))
        return cur.fetchall()
