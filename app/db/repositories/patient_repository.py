"""Patient repository for nurse search/registration workflow."""

from __future__ import annotations

from typing import Any

from app.db.connection import get_db_cursor


def search_patient_profiles(keyword: str) -> list[dict[str, Any]]:
    key = f"%{keyword}%"
    with get_db_cursor() as cur:
        cur.execute(
            """
            SELECT
                patient_profile_id,
                user_id,
                patient_category,
                full_name,
                institutional_email,
                contact_number
            FROM patient_profiles
            WHERE full_name LIKE %s
               OR institutional_email LIKE %s
               OR contact_number LIKE %s
            ORDER BY full_name ASC
            LIMIT 30
            """,
            (key, key, key),
        )
        return cur.fetchall()


def get_patient_profile_by_id(patient_profile_id: int) -> dict[str, Any] | None:
    with get_db_cursor() as cur:
        cur.execute(
            """
            SELECT
                patient_profile_id,
                user_id,
                patient_category,
                full_name,
                institutional_email,
                contact_number,
                student_course,
                student_year_level,
                faculty_staff_department
            FROM patient_profiles
            WHERE patient_profile_id = %s
            LIMIT 1
            """,
            (patient_profile_id,),
        )
        return cur.fetchone()


def get_patient_profile_by_user_id(user_id: int) -> dict[str, Any] | None:
    with get_db_cursor() as cur:
        cur.execute(
            """
            SELECT
                patient_profile_id,
                user_id,
                patient_category,
                full_name,
                institutional_email,
                contact_number,
                student_course,
                student_year_level,
                faculty_staff_department,
                allergies,
                known_conditions,
                current_medications
            FROM patient_profiles
            WHERE user_id = %s
            LIMIT 1
            """,
            (user_id,),
        )
        return cur.fetchone()


def create_patient_profile_for_walkin(
    *,
    patient_category: str,
    full_name: str,
    institutional_email: str,
    contact_number: str | None,
    student_course: str | None = None,
    student_year_level: int | None = None,
    faculty_staff_department: str | None = None,
) -> int | None:
    with get_db_cursor() as cur:
        cur.execute(
            """
            INSERT INTO patient_profiles (
                user_id,
                patient_category,
                full_name,
                institutional_email,
                contact_number,
                student_course,
                student_year_level,
                faculty_staff_department
            ) VALUES (NULL, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                patient_category,
                full_name,
                institutional_email,
                contact_number,
                student_course,
                student_year_level,
                faculty_staff_department,
            ),
        )
        return int(cur.lastrowid)


def create_patient_profile_for_user(
    *,
    user_id: int,
    patient_category: str,
    full_name: str,
    institutional_email: str,
    student_course: str | None = None,
    student_year_level: int | None = None,
    faculty_staff_department: str | None = None,
) -> int | None:
    with get_db_cursor() as cur:
        cur.execute(
            """
            INSERT INTO patient_profiles (
                user_id,
                patient_category,
                full_name,
                institutional_email,
                contact_number,
                student_course,
                student_year_level,
                faculty_staff_department
            ) VALUES (%s, %s, %s, %s, NULL, %s, %s, %s)
            """,
            (
                user_id,
                patient_category,
                full_name,
                institutional_email,
                student_course,
                student_year_level,
                faculty_staff_department,
            ),
        )
        return int(cur.lastrowid)


def update_patient_profile(
    *,
    patient_profile_id: int,
    full_name: str | None = None,
    contact_number: str | None = None,
    allergies: str | None = None,
    known_conditions: str | None = None,
    current_medications: str | None = None,
    student_course: str | None = None,
    student_year_level: int | None = None,
    faculty_staff_department: str | None = None,
) -> bool:
    """Update patient profile fields. Only provided fields are updated."""
    with get_db_cursor() as cur:
        updates = []
        params = []

        if full_name is not None:
            updates.append("full_name = %s")
            params.append(full_name)
        if contact_number is not None:
            updates.append("contact_number = %s")
            params.append(contact_number)
        if allergies is not None:
            updates.append("allergies = %s")
            params.append(allergies)
        if known_conditions is not None:
            updates.append("known_conditions = %s")
            params.append(known_conditions)
        if current_medications is not None:
            updates.append("current_medications = %s")
            params.append(current_medications)
        if student_course is not None:
            updates.append("student_course = %s")
            params.append(student_course)
        if student_year_level is not None:
            updates.append("student_year_level = %s")
            params.append(student_year_level)
        if faculty_staff_department is not None:
            updates.append("faculty_staff_department = %s")
            params.append(faculty_staff_department)

        if not updates:
            return True  # No updates requested

        params.append(patient_profile_id)
        update_clause = ", ".join(updates)

        cur.execute(
            f"""
            UPDATE patient_profiles
            SET {update_clause}
            WHERE patient_profile_id = %s
            """,
            params,
        )

        return cur.rowcount > 0
