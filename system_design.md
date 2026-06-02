# System Design
## BatStateU CliniCare: Flask Project Structure and Page/Module Plan

This system design follows the approved project scope, final database design, final MySQL schema, and stored procedures/triggers as the source of truth.

---

## 1. Recommended Project Folder Structure

```text
batstateu-clinicare/
│
├─ app/
│  ├─ __init__.py
│  ├─ config.py
│  ├─ extensions.py
│  ├─ auth/
│  │  ├─ decorators.py
│  │  ├─ routes.py
│  │  ├─ services.py
│  │  └─ navigation.py
│  ├─ db/
│  │  ├─ connection.py
│  │  └─ repositories/
│  ├─ modules/
│  │  ├─ patient/
│  │  ├─ nurse/
│  │  ├─ physician/
│  │  ├─ clinic_admin/
│  │  └─ system_admin/
│  ├─ services/
│  ├─ utils/
│  ├─ static/
│  │  ├─ css/
│  │  ├─ js/
│  │  └─ img/
│  └─ templates/
│     ├─ layouts/
│     ├─ includes/
│     ├─ auth/
│     ├─ patient/
│     ├─ nurse/
│     ├─ physician/
│     ├─ clinic_admin/
│     └─ system_admin/
│
├─ database/
├─ instance/
├─ logs/
├─ tests/
├─ run.py
├─ requirements.txt
└─ .env / .env.example
```

---

## 2. Core Python/Flask Files and Their Purpose

- `run.py` — local entry point that runs the Flask app.
- `app/__init__.py` — application factory, blueprint registration.
- `app/config.py` — environment-based configuration.
- `app/extensions.py` — shared Flask extensions wiring.
- `app/auth/routes.py` — login, registration, verification flows.
- `app/db/connection.py` — MySQL connection + cursor context manager.
- `app/db/repositories/*` — data access layer per entity.
- `app/services/visit_workflow_service.py` — visit-centric workflow logic.

---

## 3. Shared Files Needed by the System

### Database Connection
- `app/db/connection.py`

### Authentication / Session Handling
- `app/auth/decorators.py`
- `app/auth/services.py`

### Authorization Checks
- `app/auth/decorators.py`

### Reusable Layout Files
- `app/templates/layouts/base.html`
- `app/templates/includes/topbar.html`
- `app/templates/includes/sidebar.html`
- `app/templates/includes/flash_messages.html`

---

## 4. Main Modules/Pages for Each Role

### patient_user
- Dashboard
- My Profile
- My Appointments (request/list/detail)
- My Visit/Clinic Record History (read-only)

### clinic_nurse
- Dashboard (pending requests + queue)
- Patient Search/Register/Update
- Appointment Review (approve/adjust/decline)
- Check-in Page
- Create Visit from Checked-in Appointment
- Walk-in/Emergency Visit Registration
- Triage Entry and Queue Management

### physician
- Dashboard (assigned queue)
- Visit Detail (central encounter page)
- Consultation Create/Edit/Complete
- Patient Clinical History View

### clinic_admin
- Operations Dashboard
- Appointment/Visit/Consultation Monitoring (read-focused)
- De-identified Reports
- Audit Logs (read/filter)

### system_admin
- User Account Management
- Role Assignment
- Account Activation/Deactivation
- Lookup Management (triage levels, consultation types)
- System Configuration
- Audit Logs (full access)

---

## 5. Suggested Navigation/Menu Structure

### Common
- Dashboard
- Profile
- Logout

### patient_user
- My Appointments
- My Clinic Records

### clinic_nurse
- Patients
- Appointment Requests
- Check-in
- Walk-in/Emergency
- Triage Queue

### physician
- My Queue
- Consultations

### clinic_admin
- Operations Overview
- Reports
- Audit Logs

### system_admin
- Users & Roles
- Lookup Management
- System Config
- Audit Logs

---

## 6. Suggested Page Flow

### Registration and Email Verification
Register → Pending Verification Notice → Email Verification Link → Account Activated

### Login / Logout
Login → Role-based Dashboard → Logout

### Appointment Request and Approval
Patient submits request → Nurse/Admin reviews → Approve/Adjust/Decline → Scheduled list updates

### Check-in and Visit Creation
Nurse checks in approved appointment → Create `visits` row from checked-in appointment

### Walk-in / Emergency Handling
Nurse finds/creates patient profile → Create walk-in/emergency `visits` row → Triage and queue prioritization

### Consultation Recording
Physician opens visit → records consultation → visit completed via trigger → linked appointment completed (if applicable)

### Reports and Audit Logs
Admin/System Admin opens report filters → view de-identified summaries and audit trails

---

## 7. Which Pages Should Be CRUD Pages

- Users (admin-managed)
- Patient Profiles
- Appointments (request/update/status actions)
- Triage Records
- Consultations
- Lookup Tables
- Optional: Physician Profiles

---

## 8. Which Pages Should Be Dashboard / List / Detail / Form Pages

### Dashboard Pages
- One dashboard per role (`patient_user`, `clinic_nurse`, `physician`, `clinic_admin`, `system_admin`)

### List Pages
- Appointments, Visits Queue, Patients, Audit Logs, Reports

### Detail Pages
- Patient Detail, Appointment Detail, Visit Detail, Consultation Detail

### Form Pages
- Registration, Login, Appointment Request, Appointment Approval/Adjustment, Check-in, Visit Creation, Triage, Consultation

---

## 9. Recommended Naming Convention for Files and Folders

- Folders: lowercase with underscore (e.g., `clinic_admin`, `system_admin`)
- Modules: `routes.py` per role under `app/modules/<role>/`
- Repositories: `snake_case_repository.py` (e.g., `appointment_repository.py`)
- Services: `snake_case_service.py` (e.g., `visit_workflow_service.py`)
- Templates: lowercase snake_case per action (e.g., `appointment_review.html`)
- Routes: resource-based and action-clear (e.g., `/appointments/request`, `/visits/create-from-appointment`)

---

## 10. Practical Implementation Notes

- Keep write operations aligned with stored procedures/triggers where defined.
- Keep `visits` as the central encounter workflow in all role pages.
- Keep strict role guards at route and controller levels.
- Reuse shared validation and flash/error handling helpers.
- Keep nurse and physician responsibilities separated in controllers and views.
- Use clear handling of procedure `SIGNAL` errors for user-friendly feedback.
- Build minimum viable role pages first, then iterate UI and report polish.

---

## 11. Testing and Demo Readiness

### 11.1 First Live Testing Pass (Simplified)

Before full route-by-route testing, run this quick pass:

1. App runs successfully.
2. Login works.
3. One role redirect works correctly.

Only after the three checks pass should full testing continue.

### 11.2 Full Testing Order

1. Auth + role landing for all roles.
2. Patient appointment request flow.
3. Nurse appointment review/check-in flow.
4. Walk-in/emergency + triage flow.
5. Physician consultation flow.
6. Clinic admin operations + de-identified reports.
7. System admin user/lookup/configuration + full audit logs.
8. Unauthorized URL checks per role.

### 11.3 Pages/Routes to Open First

1. `/auth/login`
2. Role landing page after login:
	- patient: `/patient/appointments`
	- nurse: `/nurse/appointments/review`
	- physician: `/physician/queue`
	- clinic admin: `/clinic-admin/dashboard`
	- system admin: `/system-admin/users`

Then proceed module-by-module:

- Patient: `/patient/appointments/request`
- Nurse: `/nurse/appointments/<appointment_id>/review`, `/nurse/appointments/<appointment_id>/check-in`, `/nurse/visits/queue`, `/nurse/patients/search`, `/nurse/visits/walkin-emergency/register`, `/nurse/visits/<visit_id>/triage`
- Physician: `/physician/visits/<visit_id>`, `/physician/visits/<visit_id>/consultation`, `/physician/patients/<patient_profile_id>/history`
- Clinic Admin: `/clinic-admin/operations`, `/clinic-admin/reports`, `/clinic-admin/reports/appointments_status_mix`, `/clinic-admin/audit-logs`
- System Admin: `/system-admin/lookups?type=triage`, `/system-admin/lookups?type=consultation`, `/system-admin/configuration`, `/system-admin/audit-logs`

### 11.4 Sample Demo Data Plan by Role

- `patient_user`: 1 active user, linked patient profile, pending/approved appointment samples.
- `clinic_nurse`: 1 active user, pending + approved appointments, one walk-in/emergency case.
- `physician`: 1 active user, assigned queue visits, at least one triaged visit.
- `clinic_admin`: 1 active user, enough cross-module records for dashboards/reports.
- `system_admin`: 1 active user, complete users/roles/lookups, broad audit activity.

### 11.5 Minimum Records Needed for Smooth Demo

- `roles`: 5 (patient_user, clinic_nurse, physician, clinic_admin, system_admin)
- `users`: 8-10
- `patient_profiles`: 3-4
- `lookup_triage_levels`: **routine, urgent, emergency**
- `lookup_consultation_types`: 4-6 (include walk-in and emergency values)
- `appointments`: 4-6
- `visits`: 4-6
- `triage_records`: 2-3
- `consultations`: 2-3
- `audit_logs`: 20+

### 11.6 Recommended Demo Walkthrough Script (Presentation Order)

1. Login + role-based redirect proof.
2. Patient requests appointment.
3. Nurse reviews/approves/checks in and creates visit.
4. Nurse demonstrates walk-in/emergency registration + triage.
5. Physician opens queue, records consultation.
6. Clinic admin shows operations dashboard + de-identified reports.
7. System admin shows users/lookups/configuration + full audit logs.
8. End with one unauthorized URL test to show route guard behavior.

