"""Service helpers for persistent system configuration."""

from __future__ import annotations

from app.db.repositories.settings_repository import get_setting, set_setting

SETTINGS_REPORTS_DEFAULT_DAYS = "reports_default_days"
SETTINGS_AUDIT_LOG_LIMIT = "audit_log_limit"
SETTINGS_ALLOWED_EMAIL_DOMAINS = "allowed_email_domains"

DEFAULT_REPORTS_DEFAULT_DAYS = "30"
DEFAULT_AUDIT_LOG_LIMIT = "300"
DEFAULT_ALLOWED_EMAIL_DOMAINS = "batstate-u.edu.ph,g.batstate-u.edu.ph"


def normalize_email_domains(raw_domains: str | None) -> str:
    """Normalize and deduplicate configured domains into CSV."""
    if not raw_domains:
        return DEFAULT_ALLOWED_EMAIL_DOMAINS

    seen: set[str] = set()
    ordered: list[str] = []
    for raw in raw_domains.replace("\n", ",").split(","):
        domain = raw.strip().lower()
        if not domain or domain in seen:
            continue
        seen.add(domain)
        ordered.append(domain)

    if not ordered:
        return DEFAULT_ALLOWED_EMAIL_DOMAINS
    return ",".join(ordered)


def get_allowed_email_domains() -> tuple[str, ...]:
    csv_value = get_setting(SETTINGS_ALLOWED_EMAIL_DOMAINS, DEFAULT_ALLOWED_EMAIL_DOMAINS)
    normalized_csv = normalize_email_domains(csv_value)
    return tuple(item.strip() for item in normalized_csv.split(",") if item.strip())


def get_configuration_values(app_name: str) -> dict[str, str | bool]:
    reports_default_days = get_setting(SETTINGS_REPORTS_DEFAULT_DAYS, DEFAULT_REPORTS_DEFAULT_DAYS)
    audit_log_limit = get_setting(SETTINGS_AUDIT_LOG_LIMIT, DEFAULT_AUDIT_LOG_LIMIT)
    allowed_email_domains = get_setting(SETTINGS_ALLOWED_EMAIL_DOMAINS, DEFAULT_ALLOWED_EMAIL_DOMAINS)

    return {
        "app_name": app_name,
        "reports_default_days": reports_default_days or DEFAULT_REPORTS_DEFAULT_DAYS,
        "audit_log_limit": audit_log_limit or DEFAULT_AUDIT_LOG_LIMIT,
        "allowed_email_domains": normalize_email_domains(allowed_email_domains),
    }


def save_configuration_values(
    *,
    reports_default_days: str,
    audit_log_limit: str,
    allowed_email_domains: str,
) -> None:
    set_setting(SETTINGS_REPORTS_DEFAULT_DAYS, reports_default_days.strip() or DEFAULT_REPORTS_DEFAULT_DAYS)
    set_setting(SETTINGS_AUDIT_LOG_LIMIT, audit_log_limit.strip() or DEFAULT_AUDIT_LOG_LIMIT)
    set_setting(SETTINGS_ALLOWED_EMAIL_DOMAINS, normalize_email_domains(allowed_email_domains))
