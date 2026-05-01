/* ============================================================
   BatStateU CliniCare - Demo Seed Data (MySQL)
   Aligned to approved schema and testing/demo plan
   ============================================================ */

SET NAMES utf8mb4;
SET time_zone = '+00:00';

/*
  IMPORTANT:
  users.password_hash must be a valid Werkzeug hash.
   Generated for demo password: Demo@123
*/
SET @DEMO_HASH = 'scrypt:32768:8:1$yl33sjS0zo33rMif$778b6d45ae53b4d6f69441c2672065a35b51779ace6af2d8b487c5cc57934627447d1e94edce637ad67a4edb7b1404b27910cb9ae81a8a25d0515b176de9e46d';

/* ------------------------------------------------------------
   roles
   ------------------------------------------------------------ */
INSERT INTO roles (role_id, role_name) VALUES
(1, 'patient_user'),
(2, 'clinic_nurse'),
(3, 'physician'),
(5, 'clinic_admin'),
(6, 'system_admin')
ON DUPLICATE KEY UPDATE role_name = VALUES(role_name);

/* ------------------------------------------------------------
   users
   ------------------------------------------------------------ */
INSERT INTO users (user_id, institutional_email, password_hash, role_id, account_status, created_at, updated_at) VALUES
(1, 'system.admin@g.batstate-u.edu.ph', @DEMO_HASH, 6, 'active', '2026-04-01 08:00:00', '2026-04-01 08:00:00'),
(2, 'clinic.admin@g.batstate-u.edu.ph', @DEMO_HASH, 5, 'active', '2026-04-01 08:05:00', '2026-04-01 08:05:00'),
(3, 'nurse.one@g.batstate-u.edu.ph', @DEMO_HASH, 2, 'active', '2026-04-01 08:10:00', '2026-04-01 08:10:00'),
(4, 'dr.santos@g.batstate-u.edu.ph', @DEMO_HASH, 3, 'active', '2026-04-01 08:15:00', '2026-04-01 08:15:00'),
(6, 'juan.patient@g.batstate-u.edu.ph', @DEMO_HASH, 1, 'active', '2026-04-01 08:25:00', '2026-04-01 08:25:00'),
(7, 'maria.patient@g.batstate-u.edu.ph', @DEMO_HASH, 1, 'active', '2026-04-01 08:30:00', '2026-04-01 08:30:00'),
(8, 'dr.reyes@g.batstate-u.edu.ph', @DEMO_HASH, 3, 'active', '2026-04-01 08:35:00', '2026-04-01 08:35:00'),
(9, 'nurse.two@g.batstate-u.edu.ph', @DEMO_HASH, 2, 'inactive', '2026-04-01 08:40:00', '2026-04-01 08:40:00')
ON DUPLICATE KEY UPDATE
institutional_email = VALUES(institutional_email),
password_hash = VALUES(password_hash),
role_id = VALUES(role_id),
account_status = VALUES(account_status);

/*
   OPTIONAL: Verification workflow demo seed
   Enable this block only when you want to demonstrate pending verification flow.
   Keep disabled for simpler active-user demo login.

INSERT INTO users (user_id, institutional_email, password_hash, role_id, account_status, created_at, updated_at)
VALUES (10, 'pending.user@g.batstate-u.edu.ph', @DEMO_HASH, 1, 'pending_verification', '2026-04-11 10:10:00', '2026-04-11 10:10:00')
ON DUPLICATE KEY UPDATE
institutional_email = VALUES(institutional_email),
password_hash = VALUES(password_hash),
role_id = VALUES(role_id),
account_status = VALUES(account_status);

INSERT INTO email_verifications (verification_id, user_id, token, expires_at, verified_at)
VALUES (1, 10, 'demo-verify-token-001', DATE_ADD(UTC_TIMESTAMP(), INTERVAL 24 HOUR), NULL)
ON DUPLICATE KEY UPDATE
token = VALUES(token),
expires_at = VALUES(expires_at),
verified_at = VALUES(verified_at);
*/

/* ------------------------------------------------------------
   patient_profiles
   ------------------------------------------------------------ */
INSERT INTO patient_profiles (
  patient_profile_id, user_id, patient_category, full_name, institutional_email,
  student_course, student_year_level, faculty_staff_department, contact_number,
  emergency_contact_name, emergency_contact_number, allergies, known_conditions,
  current_medications, consent_acknowledged_at
) VALUES
(1, 6, 'student', 'Juan Dela Cruz', 'juan.patient@g.batstate-u.edu.ph',
 'BSIT', '3', NULL, '09171234567', 'Pedro Dela Cruz', '09170000001',
 'None', 'Mild asthma', 'Salbutamol PRN', '2026-04-01 09:00:00'),

(2, 7, 'faculty', 'Maria Santos', 'maria.patient@g.batstate-u.edu.ph',
 NULL, NULL, 'College of Engineering', '09181234567', 'Jose Santos', '09180000002',
 'Penicillin', 'Hypertension', 'Losartan 50mg daily', '2026-04-01 09:05:00'),

(3, NULL, 'staff', 'Jose Ramirez', 'jose.ramirez@batstate-u.edu.ph',
 NULL, NULL, 'Registrar Office', '09191234567', 'Liza Ramirez', '09190000003',
 NULL, NULL, NULL, '2026-04-02 10:00:00'),

(4, NULL, 'student', 'Ana Lopez', 'ana.lopez@g.batstate-u.edu.ph',
 'BSN', '2', NULL, '09991234567', 'Rosa Lopez', '09990000004',
 'Seafood', NULL, NULL, '2026-04-03 11:00:00')
ON DUPLICATE KEY UPDATE
full_name = VALUES(full_name),
institutional_email = VALUES(institutional_email);

/* ------------------------------------------------------------
   lookup_triage_levels (approved values)
   ------------------------------------------------------------ */
INSERT INTO lookup_triage_levels (triage_level_id, code, display_name, is_active) VALUES
(1, 'routine',   'Routine',   1),
(2, 'urgent',    'Urgent',    1),
(3, 'emergency', 'Emergency', 1)
ON DUPLICATE KEY UPDATE
code = VALUES(code),
display_name = VALUES(display_name),
is_active = VALUES(is_active);

/* ------------------------------------------------------------
   lookup_consultation_types
   ------------------------------------------------------------ */
INSERT INTO lookup_consultation_types (consultation_type_id, code, display_name, is_active) VALUES
(1, 'appointment', 'Appointment Consultation', 1),
(2, 'walk_in',     'Walk-In Consultation',     1),
(3, 'emergency',   'Emergency Consultation',   1),
(4, 'follow_up',   'Follow-Up Consultation',   1)
ON DUPLICATE KEY UPDATE
code = VALUES(code),
display_name = VALUES(display_name),
is_active = VALUES(is_active);

/* ------------------------------------------------------------
   appointments
   ------------------------------------------------------------ */
INSERT INTO appointments (
  appointment_id, patient_profile_id, physician_user_id, requested_by_user_id,
  scheduled_date, scheduled_time, reason, consultation_type_id, status,
  approved_by_user_id, created_at, updated_at
) VALUES
(1, 1, 4, 6, '2026-04-15', '09:00:00', 'Headache and mild fever', 1, 'pending', NULL, '2026-04-10 08:00:00', '2026-04-10 08:00:00'),
(2, 2, 4, 7, '2026-04-14', '10:00:00', 'Follow-up BP monitoring', 1, 'approved', 3, '2026-04-09 09:00:00', '2026-04-10 09:15:00'),
(3, 1, 8, 6, '2026-04-11', '08:30:00', 'Chest tightness check', 1, 'checked_in', 3, '2026-04-10 07:00:00', '2026-04-11 08:35:00'),
(4, 2, 8, 7, '2026-04-13', '13:00:00', 'General consultation', 1, 'cancelled', 3, '2026-04-09 11:00:00', '2026-04-10 12:00:00')
ON DUPLICATE KEY UPDATE
status = VALUES(status),
approved_by_user_id = VALUES(approved_by_user_id),
updated_at = VALUES(updated_at);

/* ------------------------------------------------------------
   visits
   ------------------------------------------------------------ */
INSERT INTO visits (
  visit_id, patient_profile_id, physician_user_id, consultation_type_id,
  source_appointment_id, arrival_time, triage_level_id, visit_status,
  created_by_user_id, created_at, updated_at
) VALUES
(1, 1, 8, 1, 3, '2026-04-11 08:40:00', 2, 'completed', 3, '2026-04-11 08:40:00', '2026-04-11 09:20:00'),
(2, 3, 4, 2, NULL, '2026-04-11 09:10:00', 1, 'queued', 3, '2026-04-11 09:10:00', '2026-04-11 09:10:00'),
(3, 4, 8, 3, NULL, '2026-04-11 09:05:00', 3, 'queued', 3, '2026-04-11 09:05:00', '2026-04-11 09:05:00'),
(4, 2, 4, 1, NULL, '2026-04-08 14:00:00', 1, 'completed', 3, '2026-04-08 14:00:00', '2026-04-08 14:40:00')
ON DUPLICATE KEY UPDATE
visit_status = VALUES(visit_status),
updated_at = VALUES(updated_at);

/* ------------------------------------------------------------
   triage_records
   ------------------------------------------------------------ */
INSERT INTO triage_records (
  triage_id, visit_id, bp, heart_rate, respiratory_rate, temperature, oxygen_saturation,
  weight, initial_assessment, immediate_action, referral_details,
  emergency_contact_notified, emergency_contact_notified_at, notes
) VALUES
(1, 1, '130/85', 92, 20, 37.3, 97, 62.50, 'Mild respiratory discomfort', 'Observed and prepared for physician review', NULL, 0, NULL, 'Stable on assessment'),
(2, 2, '120/80', 84, 18, 36.9, 99, 70.10, 'Walk-in, non-urgent symptoms', 'Placed in routine queue', NULL, 0, NULL, 'No red flags'),
(3, 3, '150/95', 118, 26, 38.5, 93, 55.20, 'Possible acute respiratory distress', 'Prioritized to emergency queue', 'Possible ER transfer if deterioration continues', 1, '2026-04-11 09:08:00', 'Guardian informed')
ON DUPLICATE KEY UPDATE
initial_assessment = VALUES(initial_assessment),
immediate_action = VALUES(immediate_action);

/* ------------------------------------------------------------
   consultations
   ------------------------------------------------------------ */
INSERT INTO consultations (
  consultation_id, visit_id, history, physical_exam, assessment, `plan`,
  follow_up_instructions, created_by_physician_id, created_at, updated_at
) VALUES
(1, 1, '2-day chest tightness and cough', 'Mild wheeze, no cyanosis', 'Acute bronchospasm, stable',
 'Prescribe bronchodilator and supportive meds', 'Return if symptoms worsen within 24h', 8, '2026-04-11 09:15:00', '2026-04-11 09:15:00'),
(2, 4, 'Routine BP follow-up', 'BP controlled, no edema', 'Stable hypertension',
 'Continue maintenance therapy', 'Follow-up in 2 weeks', 4, '2026-04-08 14:20:00', '2026-04-08 14:20:00')
ON DUPLICATE KEY UPDATE
assessment = VALUES(assessment),
`plan` = VALUES(`plan`);

/* ------------------------------------------------------------
   audit_logs
   ------------------------------------------------------------ */
INSERT INTO audit_logs (
  audit_log_id, user_id, action_type, entity_type, entity_id, description, performed_at, ip_address
) VALUES
(1, 6, 'appointment_requested', 'appointments', 1, 'Patient requested appointment #1', '2026-04-10 08:00:30', '127.0.0.1'),
(2, 3, 'appointment_updated', 'appointments', 2, 'Nurse approved appointment #2', '2026-04-10 09:15:00', '127.0.0.1'),
(3, 3, 'appointment_checked_in', 'appointments', 3, 'Checked in appointment #3', '2026-04-11 08:35:00', '127.0.0.1'),
(4, 3, 'visit_created_from_appointment', 'visits', 1, 'Created visit #1 from appointment #3', '2026-04-11 08:40:10', '127.0.0.1'),
(5, 3, 'visit_created_walkin_emergency', 'visits', 3, 'Created emergency walk-in visit #3', '2026-04-11 09:05:10', '127.0.0.1'),
(6, 8, 'consultation_created', 'consultations', 1, 'Physician created consultation for visit #1', '2026-04-11 09:15:30', '127.0.0.1'),
(7, 1, 'user_updated', 'users', 9, 'System admin updated nurse.two account status', '2026-04-11 10:00:00', '127.0.0.1'),
(8, 1, 'lookup_updated', 'lookup_consultation', 3, 'System admin validated emergency consultation lookup', '2026-04-11 10:05:00', '127.0.0.1')
ON DUPLICATE KEY UPDATE
description = VALUES(description),
performed_at = VALUES(performed_at);

/* ============================================================
   Short notes: demo support mapping

   Patient appointment request flow:
   - users: 6, 7
   - patient_profiles: 1, 2
   - appointments: 1 (pending), 2 (approved), 3 (checked_in)

   Nurse review/check-in flow:
   - users: 3
   - appointments: 1, 2, 3, 4
   - audit_logs: 2, 3

   Walk-in/emergency triage flow:
   - patient_profiles: 3, 4
   - visits: 2 (walk-in queued), 3 (emergency queued)
   - lookup_triage_levels: routine, urgent, emergency
   - triage_records: 2, 3

    Physician consultation flow:
    - users: 4, 8
    - visits: 1, 4 completed examples
    - consultations: 1, 2

    Clinic admin reports:
    - mixed states/timestamps across appointments, visits,
       consultations, audit_logs

   System admin pages:
   - roles, users (active/inactive mix), lookups, audit logs
   ============================================================ */
