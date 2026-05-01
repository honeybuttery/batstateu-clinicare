# System Design
## BatStateU CliniCare: PHP Project Structure and Page/Module Plan

This system design follows the approved project scope, final database design, final MySQL schema, and stored procedures/triggers as the source of truth.

---

## 1. Recommended Project Folder Structure

```text
batstateu-clinicare/
│
├─ public/
│  ├─ index.php
│  ├─ .htaccess
│  └─ assets/
│     ├─ css/
│     ├─ js/
│     └─ img/
│
├─ app/
│  ├─ config/
│  │  ├─ app.php
│  │  ├─ database.php
│  │  └─ constants.php
│  │
│  ├─ core/
│  │  ├─ Router.php
│  │  ├─ Controller.php
│  │  ├─ View.php
│  │  ├─ Session.php
│  │  ├─ Auth.php
│  │  └─ Authorization.php
│  │
│  ├─ helpers/
│  │  ├─ functions.php
│  │  └─ validation.php
│  │
│  ├─ models/
│  │  ├─ User.php
│  │  ├─ PatientProfile.php
│  │  ├─ Appointment.php
│  │  ├─ Visit.php
│  │  ├─ TriageRecord.php
│  │  ├─ Consultation.php
│  │  ├─ AuditLog.php
│  │  └─ Lookup*.php
│  │
│  ├─ services/
│  │  ├─ AuditService.php
│  │  └─ VisitWorkflowService.php
│  │
│  ├─ controllers/
│  │  ├─ AuthController.php
│  │  ├─ PatientController.php
│  │  ├─ NurseController.php
│  │  ├─ PhysicianController.php
│  │  ├─ AdminClinicController.php
│  │  ├─ AdminSystemController.php
│  │  ├─ AppointmentController.php
│  │  ├─ VisitController.php
│  │  ├─ ConsultationController.php
│  │  └─ ReportController.php
│  │
│  └─ views/
│     ├─ layouts/
│     ├─ shared/
│     ├─ auth/
│     ├─ patient/
│     ├─ nurse/
│     ├─ physician/
│     ├─ admin_clinic/
│     └─ admin_system/
│
├─ storage/
│  ├─ logs/
│  └─ uploads/
│
└─ vendor/   (if Composer is used)
```

---

## 2. Core PHP Files and Their Purpose

- `public/index.php` — bootstrap + route dispatch entry point.
- `app/core/Router.php` — URL-to-controller/action mapping.
- `app/core/Auth.php` — login state, current `user_id`, role retrieval.
- `app/core/Authorization.php` — role-based route/action guards.
- `app/config/database.php` — PDO connection and DB settings.
- `app/services/VisitWorkflowService.php` — central `visits` workflow operations.
- `app/services/AuditService.php` — centralized audit calls.

---

## 3. Shared Files Needed by the System

### Database Connection
- `app/config/database.php`

### Authentication / Session Handling
- `app/core/Session.php`
- `app/core/Auth.php`

### Authorization Checks
- `app/core/Authorization.php`

### Reusable Layout Files
- `app/views/layouts/main.php`
- `app/views/layouts/auth.php`
- `app/views/shared/topbar.php`
- `app/views/shared/sidebar.php`
- `app/views/shared/flash_messages.php`

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

- Folders: lowercase with underscore (e.g., `admin_system`, `admin_clinic`)
- Controllers: `PascalCaseController.php`
- Models: `PascalCase.php`
- Views: lowercase snake_case per action (e.g., `appointment_review.php`)
- Routes: resource-based and action-clear (e.g., `/appointments/request`, `/visits/create-from-appointment`)
- Services: workflow-oriented names (`VisitWorkflowService`)

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

