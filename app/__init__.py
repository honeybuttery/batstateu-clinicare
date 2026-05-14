"""Application factory for BatStateU CliniCare."""

import secrets
from hmac import compare_digest

from dotenv import load_dotenv
from flask import Flask, flash, redirect, render_template, request, session, url_for

from .auth import init_auth
from .auth.navigation import get_role_home_endpoint
from .config import Config
from .extensions import init_extensions
from .modules import register_blueprints
from .utils.display_labels import format_display_label, format_local_datetime, format_time_12h


def create_app(config_class: type[Config] = Config) -> Flask:
    """Create and configure the Flask app instance."""
    load_dotenv(override=True)

    app = Flask(__name__, instance_relative_config=True)
    app.config.from_object(config_class)

    if not app.config.get("SECRET_KEY"):
        app.config["SECRET_KEY"] = secrets.token_hex(32)
        app.logger.warning("SECRET_KEY is not set in environment. Using temporary runtime key.")

    init_extensions(app)
    init_auth(app)
    register_blueprints(app)

    @app.context_processor
    def inject_navigation_helpers():
        csrf_token = session.get("_csrf_token")
        if not csrf_token:
            csrf_token = secrets.token_urlsafe(32)
            session["_csrf_token"] = csrf_token

        role_name = session.get("role_name")
        role_home_endpoint = get_role_home_endpoint(role_name)
        return {
            "role_home_endpoint": role_home_endpoint,
            "role_home_url": url_for(role_home_endpoint),
            "csrf_token": csrf_token,
            "format_display_label": format_display_label,
        }

    @app.template_filter("display_label")
    def display_label_filter(value):
        return format_display_label(value)

    @app.template_filter("time_12h")
    def time_12h_filter(value):
        return format_time_12h(value)

    @app.template_filter("local_dt")
    def local_dt_filter(value):
        return format_local_datetime(value)

    @app.before_request
    def validate_csrf_token():
        if request.method != "POST":
            return None

        session_token = session.get("_csrf_token")
        request_token = request.form.get("csrf_token") or request.headers.get("X-CSRF-Token")

        if not session_token or not request_token or not compare_digest(session_token, request_token):
            flash("Your session form token is invalid. Please try again.", "danger")
            if session.get("user_id"):
                return redirect(url_for(get_role_home_endpoint(session.get("role_name"))))
            return redirect(url_for("auth.login_page"))

        return None

    @app.errorhandler(403)
    def forbidden(_error):
        flash("You are not authorized to access that page.", "danger")
        role_name = session.get("role_name")
        return redirect(url_for(get_role_home_endpoint(role_name)))

    @app.errorhandler(404)
    def not_found(_error):
        # Keep this simple for demo flow: logged-in users go to their role home,
        # guests are redirected to login.
        if session.get("user_id"):
            flash("Page not found.", "warning")
            return redirect(url_for(get_role_home_endpoint(session.get("role_name"))))
        return render_template("auth/login.html", page_title="Login"), 404

    @app.errorhandler(500)
    def server_error(_error):
        if request.endpoint != "auth.login_page":
            flash("Unexpected server error. Please try again.", "danger")
        if session.get("user_id"):
            return redirect(url_for(get_role_home_endpoint(session.get("role_name"))))
        return redirect(url_for("auth.login_page"))

    return app
