"""User repository for system admin management."""

from __future__ import annotations

from typing import Any

from app.db.connection import get_db_cursor


def list_roles() -> list[dict[str, Any]]:
    with get_db_cursor() as cur:
        cur.execute("SELECT role_id, role_name FROM roles ORDER BY role_name ASC")
        return cur.fetchall()


def list_users() -> list[dict[str, Any]]:
    with get_db_cursor() as cur:
        cur.execute(
            """
            SELECT
                u.user_id,
                u.institutional_email,
                u.role_id,
                r.role_name,
                u.account_status,
                u.created_at,
                u.updated_at
            FROM users u
            JOIN roles r ON r.role_id = u.role_id
            ORDER BY u.created_at DESC
            """
        )
        return cur.fetchall()


def get_user_by_id(user_id: int) -> dict[str, Any] | None:
    with get_db_cursor() as cur:
        cur.execute(
            """
            SELECT
                user_id,
                institutional_email,
                password_hash,
                role_id,
                account_status,
                created_at,
                updated_at
            FROM users
            WHERE user_id = %s
            LIMIT 1
            """,
            (user_id,),
        )
        return cur.fetchone()


def create_user(
    *,
    institutional_email: str,
    password_hash: str,
    role_id: int,
    account_status: str,
) -> int:
    with get_db_cursor() as cur:
        cur.execute(
            """
            INSERT INTO users (institutional_email, password_hash, role_id, account_status)
            VALUES (%s, %s, %s, %s)
            """,
            (institutional_email, password_hash, role_id, account_status),
        )
        return int(cur.lastrowid)


def update_user(
    *,
    user_id: int,
    institutional_email: str,
    role_id: int,
    account_status: str,
    password_hash: str | None,
) -> bool:
    with get_db_cursor() as cur:
        if password_hash:
            cur.execute(
                """
                UPDATE users
                SET institutional_email = %s,
                    role_id = %s,
                    account_status = %s,
                    password_hash = %s
                WHERE user_id = %s
                """,
                (institutional_email, role_id, account_status, password_hash, user_id),
            )
        else:
            cur.execute(
                """
                UPDATE users
                SET institutional_email = %s,
                    role_id = %s,
                    account_status = %s
                WHERE user_id = %s
                """,
                (institutional_email, role_id, account_status, user_id),
            )
        return cur.rowcount > 0
