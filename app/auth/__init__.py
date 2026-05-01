"""Auth package and blueprint registration helper."""

from flask import Flask

from .routes import bp


def init_auth(app: Flask) -> None:
	"""Register auth blueprint on the Flask app."""
	app.register_blueprint(bp)
