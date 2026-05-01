"""Repository helpers for persistent system settings."""

from __future__ import annotations

from app.db.connection import get_db_cursor


def _ensure_settings_table() -> None:
    """Create settings table if it does not exist yet."""
    with get_db_cursor() as cur:
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS system_settings (
                setting_key VARCHAR(100) NOT NULL,
                setting_value TEXT NOT NULL,
                updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                PRIMARY KEY (setting_key)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            """
        )


def get_setting(setting_key: str, default: str | None = None) -> str | None:
    _ensure_settings_table()
    with get_db_cursor() as cur:
        cur.execute(
            """
            SELECT setting_value
            FROM system_settings
            WHERE setting_key = %s
            LIMIT 1
            """,
            (setting_key,),
        )
        row = cur.fetchone()
        if not row:
            return default
        return row["setting_value"]


def set_setting(setting_key: str, setting_value: str) -> None:
    _ensure_settings_table()
    with get_db_cursor() as cur:
        cur.execute(
            """
            INSERT INTO system_settings (setting_key, setting_value)
            VALUES (%s, %s)
            ON DUPLICATE KEY UPDATE setting_value = VALUES(setting_value)
            """,
            (setting_key, setting_value),
        )