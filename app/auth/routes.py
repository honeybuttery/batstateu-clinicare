"""Starter authentication routes."""

from __future__ import annotations

import mysql.connector
from flask import Blueprint, current_app, flash, redirect, render_template, request, session, url_for

from .navigation import get_role_home_endpoint
from .services import authenticate_user, register_user, resend_verification_for_email, verify_account_by_otp
from app.services.audit_service import log_audit_event
from app.services.email_service import send_verification_email

bp = Blueprint("auth", __name__, url_prefix="/auth")


@bp.get("/login")
def login_page():
	return render_template("auth/login.html", page_title="Login")


@bp.post("/login")
def login():
	email = request.form.get("institutional_email", "")
	password = request.form.get("password", "")
	ip_address = request.remote_addr or "127.0.0.1"

	try:
		result = authenticate_user(email, password)
	except mysql.connector.Error:
		flash("Database is unavailable. Please make sure MySQL is running and try again.", "danger")
		return redirect(url_for("auth.login_page"))

	if not result["ok"]:
		flash(result["message"], "danger")
		return redirect(url_for("auth.login_page"))

	user = result["user"]
	session["user_id"] = user["user_id"]
	session["institutional_email"] = user["institutional_email"]
	session["role_name"] = user["role_name"]

	try:
		log_audit_event(
			user_id=int(user["user_id"]),
			action_type="login",
			entity_type="sessions",
			entity_id=None,
			description="User logged in.",
			ip_address=ip_address,
		)
	except mysql.connector.Error:
		current_app.logger.warning("Failed to write login audit log.")

	flash("Welcome back!", "success")
	return redirect(url_for(get_role_home_endpoint(user["role_name"])))


@bp.get("/logout")
def logout():
	user_id = session.get("user_id")
	ip_address = request.remote_addr or "127.0.0.1"
	if user_id:
		try:
			log_audit_event(
				user_id=int(user_id),
				action_type="logout",
				entity_type="sessions",
				entity_id=None,
				description="User logged out.",
				ip_address=ip_address,
			)
		except mysql.connector.Error:
			current_app.logger.warning("Failed to write logout audit log.")

	session.clear()
	flash("You have been logged out.", "info")
	return redirect(url_for("auth.login_page"))


@bp.get("/register")
def register_page():
	return render_template(
		"auth/register.html",
		page_title="Register",
		pending_email=session.get("pending_verification_email"),
	)


@bp.post("/register")
def register():
	email = request.form.get("institutional_email", "")
	full_name = request.form.get("full_name", "")
	password = request.form.get("password", "")
	confirm_password = request.form.get("confirm_password", "")
	patient_category = (request.form.get("patient_category") or "").strip().lower()
	student_course = (request.form.get("student_course") or "").strip() or None
	student_year_level = request.form.get("student_year_level", type=int)
	faculty_staff_department = (request.form.get("faculty_staff_department") or "").strip() or None

	if password != confirm_password:
		flash("Password and confirm password do not match.", "danger")
		return redirect(url_for("auth.register_page"))

	try:
		result = register_user(
			email,
			password,
			full_name,
			patient_category=patient_category or "student",
			student_course=student_course,
			student_year_level=student_year_level,
			faculty_staff_department=faculty_staff_department,
		)
	except mysql.connector.Error as e:
		current_app.logger.error(f"Database connection error during registration: {e}")
		flash("Database is unavailable. Please make sure MySQL is running and try again.", "danger")
		return redirect(url_for("auth.register_page"))

	if not result["ok"]:
		flash(result["message"], "danger")
		return redirect(url_for("auth.register_page"))

	otp_code = result.get("otp_code")
	user_id = result.get("user_id")
	created_new_user = bool(result.get("created_new_user", True))

	if user_id:
		try:
			action_type = "user_registered" if created_new_user else "verification_resent_from_register"
			description = (
				f"User registered with email {email}."
				if created_new_user
				else f"Verification code regenerated from register page for {email}."
			)
			log_audit_event(
				user_id=int(user_id),
				action_type=action_type,
				entity_type="users",
				entity_id=int(user_id),
				description=description,
				ip_address=request.remote_addr or "127.0.0.1",
			)
		except mysql.connector.Error:
			current_app.logger.warning("Failed to write register audit log.")

	if otp_code:
		session["pending_verification_email"] = email.strip().lower()
		email_sent = send_verification_email(email, otp_code)
		if not email_sent:
			current_app.logger.info("Verification OTP for %s (fallback log): %s", email, otp_code)

		success_message = result.get("message") or "Registration successful. Check your email for the verification code."
		if email_sent:
			flash(success_message, "success")
		else:
			flash(f"{success_message} But the email was not sent. Ask your admin to configure mail service.", "warning")
	else:
		flash("Registration successful, but verification code was not created.", "warning")
	return redirect(url_for("auth.register_page"))


@bp.get("/verify-notice")
def verify_notice():
	return redirect(url_for("auth.register_page"))


@bp.post("/resend-verification")
def resend_verification():
	email = (request.form.get("institutional_email") or session.get("pending_verification_email") or "").strip().lower()
	if not email:
		flash("Enter your institutional email to resend verification.", "warning")
		return redirect(url_for("auth.register_page"))

	session["pending_verification_email"] = email

	try:
		result = resend_verification_for_email(email)
	except mysql.connector.Error:
		flash("Database is unavailable. Please make sure MySQL is running and try again.", "danger")
		return redirect(url_for("auth.register_page"))

	if not result["ok"]:
		flash(result["message"], "warning")
		return redirect(url_for("auth.register_page"))

	otp_code = result.get("otp_code")
	if not otp_code:
		flash("Could not generate verification code. Please try again.", "danger")
		return redirect(url_for("auth.register_page"))

	email_sent = send_verification_email(email, otp_code)
	if not email_sent:
		current_app.logger.info("Resend verification OTP for %s (fallback log): %s", email, otp_code)
		flash("New verification code created, but email was not sent. Ask your admin to configure mail service.", "warning")
		return redirect(url_for("auth.register_page"))

	flash("A new verification code has been sent to your email.", "success")
	return redirect(url_for("auth.register_page"))


@bp.post("/verify-otp")
def verify_otp():
	otp_code = request.form.get("otp_code", "").strip()
	if not otp_code:
		flash("Please enter the verification code.", "warning")
		return redirect(url_for("auth.register_page"))

	try:
		result = verify_account_by_otp(otp_code)
	except mysql.connector.Error:
		flash("Database is unavailable. Please make sure MySQL is running and try again.", "danger")
		return redirect(url_for("auth.register_page"))

	if result["ok"]:
		session.pop("pending_verification_email", None)
		user_id = result.get("user_id")
		if user_id:
			try:
				log_audit_event(
					user_id=int(user_id),
					action_type="account_verified",
					entity_type="users",
					entity_id=int(user_id),
					description="User completed email verification via OTP.",
					ip_address=request.remote_addr or "127.0.0.1",
				)
			except mysql.connector.Error:
				current_app.logger.warning("Failed to write verification audit log.")

		flash(result["message"], "success")
		return redirect(url_for("auth.login_page"))

	flash(result["message"], "danger")
	return redirect(url_for("auth.register_page"))


@bp.get("/use-different-email")
def use_different_email():
	"""Clear verification state and return to registration form."""
	session.pop("pending_verification_email", None)
	return redirect(url_for("auth.register_page"))
