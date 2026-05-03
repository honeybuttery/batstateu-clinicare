# Implementation Notes
## BatStateU CliniCare - Current Flask + MySQL Implementation Status

This file was updated to reflect the current Python Flask codebase (not the old PHP starter scaffold).

---

## A. Baseline Already Implemented

### Application bootstrap and config
- [x] `run.py` local entry point
- [x] `app/__init__.py` application factory
- [x] `app/config.py` environment-based configuration
- [x] Request CSRF token validation for POST routes
- [x] Centralized auth-aware error redirects (403/404/500)

### Database access layer
- [x] `app/db/connection.py` MySQL connection + cursor context manager
- [x] Repository package under `app/db/repositories/`
- [x] SQL schema and routines files in root (`batstateu_clinicare_schema.sql`, `batstateu_clinicare_routines.sql`)

### Authentication and account verification
- [x] Login/logout routes
- [x] Registration with OTP generation flow
- [x] Resend verification flow
- [x] OTP verification flow
- [x] Role-based home redirection

### Role modules and routing
- [x] Blueprint registration for patient, nurse, physician, clinic admin, system admin
- [x] Route modules available per role under `app/modules/`
- [x] Navigation helpers and role-based decorators

### UI and static resources
- [x] Base layout and shared includes (`templates/layouts`, `templates/includes`)
- [x] Auth templates (`templates/auth`)
- [x] Module templates for nurse/patient/physician/clinic admin/system admin
- [x] Shared app assets in `app/static/css` and `app/static/js`

### Services and testing
- [x] Service layer package under `app/services/`
- [x] Email service wiring present (`app/services/email_service.py`)
- [x] Initial unit tests present (`tests/test_settings_service.py`)

---

## B. Environment and Run Checklist

1. Ensure MySQL is running.
2. Import database artifacts in this order:
	- `batstateu_clinicare_schema.sql`
	- `batstateu_clinicare_routines.sql`
	- optional seed files from `database/`
3. Configure environment values in `.env` (or copy from `.env.example`).
4. Install dependencies from `requirements.txt`.
5. Run the app using `python run.py`.

---

## C. Suggested Next Implementation Priorities

- [ ] Expand automated tests beyond settings helpers (auth, repositories, service flows).
- [ ] Add validation hardening for complex form submissions across module routes.
- [ ] Add stronger operational logging and error observability in production mode.
- [ ] Review authorization coverage on all mutating endpoints.
- [ ] Add deployment profile documentation (debug vs production configuration).

---

## D. Scope Guard

- Keep visit-centric workflow as the primary cross-role process.
- Continue using approved schema, routines, and triggers as source of truth.
- Implement features incrementally by module while preserving role boundaries.
- Avoid major architectural rewrites while stabilizing core flows.
