"""Module blueprint registration."""

from flask import Flask

from .clinic_admin import bp as clinic_admin_bp
from .nurse import bp as nurse_bp
from .patient import bp as patient_bp
from .physician import bp as physician_bp
from .system_admin import bp as system_admin_bp


def register_blueprints(app: Flask) -> None:
	"""Register all active blueprints."""
	app.register_blueprint(patient_bp)
	app.register_blueprint(nurse_bp)
	app.register_blueprint(physician_bp)
	app.register_blueprint(clinic_admin_bp)
	app.register_blueprint(system_admin_bp)
