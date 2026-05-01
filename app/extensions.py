"""Shared extension hooks (initialize later as needed)."""

from flask import Flask


def init_extensions(app: Flask) -> None:
	"""Initialize shared extensions.

	Keep this minimal for now; DB/auth extensions can be added later.
	"""
	_ = app
