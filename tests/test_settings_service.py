"""Tests for settings normalization and auth domain matching."""

import unittest

from app.auth.services import _is_institutional_email
from app.services.system_settings_service import normalize_email_domains


class SettingsServiceTests(unittest.TestCase):
    def test_normalize_email_domains_removes_whitespace_and_duplicates(self):
        raw = " batstate-u.edu.ph, g.batstate-u.edu.ph,batstate-u.edu.ph "
        normalized = normalize_email_domains(raw)
        self.assertEqual(normalized, "batstate-u.edu.ph,g.batstate-u.edu.ph")

    def test_normalize_email_domains_fallbacks_when_empty(self):
        normalized = normalize_email_domains("")
        self.assertEqual(normalized, "batstate-u.edu.ph,g.batstate-u.edu.ph")

    def test_institutional_email_validation_matches_configured_domains(self):
        domains = ("batstate-u.edu.ph", "g.batstate-u.edu.ph")
        self.assertTrue(_is_institutional_email("juan@g.batstate-u.edu.ph", domains))
        self.assertFalse(_is_institutional_email("juan@example.com", domains))


if __name__ == "__main__":
    unittest.main()
