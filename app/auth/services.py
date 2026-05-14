"""Starter authentication services aligned with final schema."""

from __future__ import annotations

import random
from datetime import datetime, timedelta, timezone
from typing import Any

from werkzeug.security import check_password_hash, generate_password_hash

from app.db.connection import get_db_cursor
from app.db.repositories.patient_repository import create_patient_profile_for_user
from app.services.system_settings_service import get_allowed_email_domains


def _utc_now() -> datetime:
	return datetime.now(timezone.utc).replace(tzinfo=None)


def _is_institutional_email(email: str, allowed_domains: tuple[str, ...]) -> bool:
	email = (email or "").strip().lower()
	if "@" not in email:
		return False
	domain = email.rsplit("@", 1)[1]
	return domain in allowed_domains


def _generate_otp() -> str:
	"""Generate a 6-digit OTP code."""
	return "".join(str(random.randint(0, 9)) for _ in range(6))


def _upsert_verification_otp(cur, user_id: int, token_valid_hours: int) -> str:
	"""Create or replace a verification OTP for a specific user.
	
	Returns: otp_code
	"""
	otp_code = _generate_otp()
	expires_at = _utc_now() + timedelta(hours=token_valid_hours)

	cur.execute("SELECT verification_id FROM email_verifications WHERE user_id = %s LIMIT 1", (user_id,))
	existing = cur.fetchone()

	if existing:
		cur.execute(
			"""
			UPDATE email_verifications
			SET otp_code = %s, expires_at = %s, verified_at = NULL
			WHERE verification_id = %s
			""",
			(otp_code, expires_at, existing["verification_id"]),
		)
	else:
		cur.execute(
			"""
			INSERT INTO email_verifications (user_id, otp_code, expires_at, verified_at)
			VALUES (%s, %s, %s, NULL)
			""",
			(user_id, otp_code, expires_at),
		)

	return otp_code


def register_user(
	institutional_email: str,
	password: str,
	full_name: str = "",
	patient_category: str = "student",
	student_course: str | None = None,
	student_year_level: int | None = None,
	faculty_staff_department: str | None = None,
	role_name: str = "patient_user",
	token_valid_hours: int = 24,
) -> dict[str, Any]:
	"""Create a pending user and verification OTP.

	Returns:
		{
			"ok": bool,
			"message": str,
			"otp_code": str | None,
			"user_id": int | None,
			"created_new_user": bool,
		}
	"""
	email = (institutional_email or "").strip().lower()
	if not email or not password:
		return {
			"ok": False,
			"message": "Email and password are required.",
			"otp_code": None,
			"user_id": None,
			"created_new_user": False,
		}

	allowed_domains = get_allowed_email_domains()
	if not _is_institutional_email(email, allowed_domains):
		return {
			"ok": False,
			"message": "Use a valid BatStateU institutional email.",
			"otp_code": None,
			"user_id": None,
			"created_new_user": False,
		}

	password_hash = generate_password_hash(password)

	if patient_category not in {"student", "faculty", "staff"}:
		return {
			"ok": False,
			"message": "Select a valid patient category.",
			"otp_code": None,
			"user_id": None,
			"created_new_user": False,
		}

	with get_db_cursor() as cur:
		# Resolve role_id from roles table.
		cur.execute("SELECT role_id FROM roles WHERE role_name = %s LIMIT 1", (role_name,))
		role_row = cur.fetchone()
		if not role_row:
			return {
				"ok": False,
				"message": "Role not found. Seed roles first.",
				"otp_code": None,
				"user_id": None,
				"created_new_user": False,
			}

		role_id = role_row["role_id"]

		# Handle existing accounts.
		cur.execute(
			"""
			SELECT user_id, account_status
			FROM users
			WHERE institutional_email = %s
			LIMIT 1
			""",
			(email,),
		)
		existing_user = cur.fetchone()
		if existing_user:
			status = existing_user["account_status"]
			existing_user_id = int(existing_user["user_id"])

			if status == "active":
				return {
					"ok": False,
					"message": "Email is already registered and active. Please log in.",
					"otp_code": None,
					"user_id": existing_user_id,
					"created_new_user": False,
				}

			if status == "inactive":
				return {
					"ok": False,
					"message": "Account is inactive. Please contact the clinic administrator.",
					"otp_code": None,
					"user_id": existing_user_id,
					"created_new_user": False,
				}

			otp_code = _upsert_verification_otp(cur, existing_user_id, token_valid_hours)
			return {
				"ok": True,
				"message": "Account already exists but is not yet verified. A new OTP has been generated.",
				"otp_code": otp_code,
				"user_id": existing_user_id,
				"created_new_user": False,
			}

		cur.execute(
			"""
			INSERT INTO users (full_name, institutional_email, password_hash, role_id, account_status)
			VALUES (%s, %s, %s, %s, 'pending_verification')
			""",
			(full_name.strip() or None, email, password_hash, role_id),
		)
		user_id = cur.lastrowid

		if role_name == "patient_user":
			profile_id = create_patient_profile_for_user(
				user_id=int(user_id),
				patient_category=patient_category,
				full_name=full_name.strip() or email,
				institutional_email=email,
				student_course=(student_course or "").strip() or None,
				student_year_level=student_year_level,
				faculty_staff_department=(faculty_staff_department or "").strip() or None,
			)
			if not profile_id:
				return {
					"ok": False,
					"message": "Failed to create patient profile.",
					"otp_code": None,
					"user_id": None,
					"created_new_user": False,
				}
		otp_code = _upsert_verification_otp(cur, int(user_id), token_valid_hours)

	return {
		"ok": True,
		"message": "Registration successful. A verification code has been sent to your email.",
		"otp_code": otp_code,
		"user_id": int(user_id),
		"created_new_user": True,
	}


def resend_verification_for_email(
	institutional_email: str,
	token_valid_hours: int = 24,
) -> dict[str, Any]:
	"""Generate a fresh OTP for a pending account."""
	email = (institutional_email or "").strip().lower()
	if not email:
		return {
			"ok": False,
			"message": "Email is required to resend verification.",
			"otp_code": None,
			"user_id": None,
		}

	with get_db_cursor() as cur:
		cur.execute(
			"""
			SELECT user_id, account_status
			FROM users
			WHERE institutional_email = %s
			LIMIT 1
			""",
			(email,),
		)
		user_row = cur.fetchone()
		if not user_row:
			return {
				"ok": False,
				"message": "No account found for that email.",
				"otp_code": None,
				"user_id": None,
			}

		if user_row["account_status"] == "active":
			return {
				"ok": False,
				"message": "Account is already active. Please log in.",
				"otp_code": None,
				"user_id": int(user_row["user_id"]),
			}

		if user_row["account_status"] == "inactive":
			return {
				"ok": False,
				"message": "Account is inactive. Please contact the clinic administrator.",
				"otp_code": None,
				"user_id": int(user_row["user_id"]),
			}

		otp_code = _upsert_verification_otp(cur, int(user_row["user_id"]), token_valid_hours)

	return {
		"ok": True,
		"message": "A new verification code is ready.",
		"otp_code": otp_code,
		"user_id": int(user_row["user_id"]),
	}


def verify_account_by_otp(otp_code: str) -> dict[str, Any]:
	"""Verify OTP and activate associated user account."""
	otp_code = (otp_code or "").strip()
	if not otp_code:
		return {"ok": False, "message": "Verification code is required.", "user_id": None}

	with get_db_cursor() as cur:
		cur.execute(
			"""
			SELECT verification_id, user_id, expires_at, verified_at
			FROM email_verifications
			WHERE otp_code = %s
			LIMIT 1
			""",
			(otp_code,),
		)
		row = cur.fetchone()
		if not row:
			return {"ok": False, "message": "Invalid verification code.", "user_id": None}

		if row["verified_at"] is not None:
			return {"ok": False, "message": "Code already used.", "user_id": int(row["user_id"])}

		if row["expires_at"] < _utc_now():
			return {"ok": False, "message": "Verification code expired.", "user_id": int(row["user_id"])}

		cur.execute(
			"UPDATE email_verifications SET verified_at = %s WHERE verification_id = %s",
			(_utc_now(), row["verification_id"]),
		)
		cur.execute(
			"UPDATE users SET account_status = 'active' WHERE user_id = %s",
			(row["user_id"],),
		)

	return {"ok": True, "message": "Account verified. You can now log in.", "user_id": int(row["user_id"])}


def authenticate_user(institutional_email: str, password: str) -> dict[str, Any]:
	"""Authenticate by institutional email + password and return user session payload."""
	email = (institutional_email or "").strip().lower()
	if not email or not password:
		return {"ok": False, "message": "Email and password are required.", "user": None}

	with get_db_cursor() as cur:
		cur.execute(
			"""
			SELECT u.user_id, u.institutional_email, u.password_hash, u.account_status, r.role_name
			FROM users u
			JOIN roles r ON r.role_id = u.role_id
			WHERE u.institutional_email = %s
			LIMIT 1
			""",
			(email,),
		)
		row = cur.fetchone()

	if not row:
		return {"ok": False, "message": "Invalid email or password.", "user": None}

	if not check_password_hash(row["password_hash"], password):
		return {"ok": False, "message": "Invalid email or password.", "user": None}

	if row["account_status"] != "active":
		return {
			"ok": False,
			"message": "Account is not active yet. Please verify your email first.",
			"user": None,
		}

	user = {
		"user_id": row["user_id"],
		"institutional_email": row["institutional_email"],
		"role_name": row["role_name"],
	}
	return {"ok": True, "message": "Login successful.", "user": user}
