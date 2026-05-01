"""Session-based auth/role decorators for route protection."""

from __future__ import annotations

from functools import wraps
from typing import Callable

from flask import flash, redirect, session, url_for

from .navigation import get_role_home_endpoint


def login_required(view: Callable):
	"""Require a logged-in session."""

	@wraps(view)
	def wrapped_view(*args, **kwargs):
		if not session.get("user_id"):
			flash("Please log in first.", "warning")
			return redirect(url_for("auth.login_page"))
		return view(*args, **kwargs)

	return wrapped_view


def role_required(*allowed_roles: str):
	"""Require logged-in user to have one of the allowed roles."""

	def decorator(view: Callable):
		@wraps(view)
		def wrapped_view(*args, **kwargs):
			if not session.get("user_id"):
				flash("Please log in to continue.", "warning")
				return redirect(url_for("auth.login_page"))

			current_role = session.get("role_name")
			if current_role not in allowed_roles:
				flash("Access denied for your role.", "danger")
				return redirect(url_for(get_role_home_endpoint(current_role)))

			return view(*args, **kwargs)

		return wrapped_view

	return decorator
