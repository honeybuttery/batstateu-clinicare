"""MySQL connection helpers for BatStateU CliniCare."""

from __future__ import annotations

from contextlib import contextmanager
from typing import Generator

import mysql.connector
from flask import current_app


def create_connection() -> mysql.connector.MySQLConnection:
	"""Create a new MySQL connection from Flask config."""
	return mysql.connector.connect(
		host=current_app.config["DB_HOST"],
		port=current_app.config["DB_PORT"],
		user=current_app.config["DB_USER"],
		password=current_app.config["DB_PASSWORD"],
		database=current_app.config["DB_NAME"],
	)


@contextmanager
def get_db_cursor(dictionary: bool = True) -> Generator:
	"""Yield a DB cursor and handle commit/rollback safely.

	Usage:
		with get_db_cursor() as cur:
			cur.execute("SELECT ...")
			rows = cur.fetchall()
	"""
	conn = create_connection()
	cursor = conn.cursor(dictionary=dictionary)
	try:
		yield cursor
		conn.commit()
	except Exception:
		conn.rollback()
		raise
	finally:
		cursor.close()
		conn.close()
