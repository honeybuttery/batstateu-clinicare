-- BatStateU CliniCare MySQL Schema (localhost prototype)
-- Source of truth: database_design.md
-- Notes:
-- - Uses user_id for account/auth linkage
-- - Uses patient_profile_id for clinical/medical tables
-- - visits is the central encounter table

SET NAMES utf8mb4;
SET time_zone = '+00:00';

-- Create database (optional)
-- CREATE DATABASE IF NOT EXISTS batstateu_clinicare CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
-- USE batstateu_clinicare;

-- -----------------------------
-- Required tables
-- -----------------------------

CREATE TABLE roles (
  role_id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  role_name VARCHAR(50) NOT NULL,
  PRIMARY KEY (role_id),
  UNIQUE KEY uq_roles_role_name (role_name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE users (
  user_id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  full_name VARCHAR(200) NULL,
  institutional_email VARCHAR(254) NOT NULL,
  password_hash VARCHAR(255) NOT NULL,
  role_id BIGINT UNSIGNED NOT NULL,
  account_status ENUM('pending_verification','active','inactive') NOT NULL DEFAULT 'pending_verification',
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (user_id),
  UNIQUE KEY uq_users_institutional_email (institutional_email),
  KEY idx_users_role_id (role_id),
  CONSTRAINT fk_users_role_id
    FOREIGN KEY (role_id) REFERENCES roles(role_id)
    ON UPDATE RESTRICT ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 1-to-1 with users enforced via UNIQUE(user_id)
CREATE TABLE email_verifications (
  verification_id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  user_id BIGINT UNSIGNED NOT NULL,
  otp_code VARCHAR(10) NOT NULL,
  expires_at DATETIME NOT NULL,
  verified_at DATETIME NULL,
  PRIMARY KEY (verification_id),
  UNIQUE KEY uq_email_verifications_user_id (user_id),
  CONSTRAINT fk_email_verifications_user_id
    FOREIGN KEY (user_id) REFERENCES users(user_id)
    ON UPDATE RESTRICT ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE lookup_triage_levels (
  triage_level_id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  code VARCHAR(50) NOT NULL,
  display_name VARCHAR(100) NOT NULL,
  is_active TINYINT(1) NOT NULL DEFAULT 1,
  PRIMARY KEY (triage_level_id),
  UNIQUE KEY uq_lookup_triage_levels_code (code)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE lookup_consultation_types (
  consultation_type_id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  code VARCHAR(50) NOT NULL,
  display_name VARCHAR(100) NOT NULL,
  is_active TINYINT(1) NOT NULL DEFAULT 1,
  PRIMARY KEY (consultation_type_id),
  UNIQUE KEY uq_lookup_consultation_types_code (code)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- patient_profiles.institutional_email is kept even when no login account exists yet.
-- When patient_profiles.user_id IS NOT NULL, it should match users.institutional_email (enforced at app layer).
CREATE TABLE patient_profiles (
  patient_profile_id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  user_id BIGINT UNSIGNED NULL,
  patient_category ENUM('student','faculty','staff') NOT NULL,
  full_name VARCHAR(200) NOT NULL,
  institutional_email VARCHAR(254) NOT NULL,
  student_course VARCHAR(150) NULL,
  student_year_level VARCHAR(50) NULL,
  faculty_staff_department VARCHAR(150) NULL,
  contact_number VARCHAR(50) NULL,
  emergency_contact_name VARCHAR(200) NULL,
  emergency_contact_number VARCHAR(50) NULL,
  allergies TEXT NULL,
  known_conditions TEXT NULL,
  current_medications TEXT NULL,
  consent_acknowledged_at DATETIME NULL,
  PRIMARY KEY (patient_profile_id),
  UNIQUE KEY uq_patient_profiles_user_id (user_id),
  UNIQUE KEY uq_patient_profiles_institutional_email (institutional_email),
  CONSTRAINT fk_patient_profiles_user_id
    FOREIGN KEY (user_id) REFERENCES users(user_id)
    ON UPDATE RESTRICT ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE appointments (
  appointment_id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  patient_profile_id BIGINT UNSIGNED NOT NULL,
  physician_user_id BIGINT UNSIGNED NOT NULL,
  requested_by_user_id BIGINT UNSIGNED NOT NULL,
  scheduled_date DATE NULL,
  scheduled_time TIME NULL,
  reason VARCHAR(255) NULL,
  consultation_type_id BIGINT UNSIGNED NOT NULL,
  status ENUM('pending','approved','checked_in','completed','cancelled','no_show') NOT NULL DEFAULT 'pending',
  approved_by_user_id BIGINT UNSIGNED NULL,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (appointment_id),
  KEY idx_appointments_patient_profile_id (patient_profile_id),
  KEY idx_appointments_physician_date_time (physician_user_id, scheduled_date, scheduled_time),
  KEY idx_appointments_status_date (status, scheduled_date),
  KEY idx_appointments_consultation_type_id (consultation_type_id),
  CONSTRAINT fk_appointments_patient_profile_id
    FOREIGN KEY (patient_profile_id) REFERENCES patient_profiles(patient_profile_id)
    ON UPDATE RESTRICT ON DELETE RESTRICT,
  CONSTRAINT fk_appointments_physician_user_id
    FOREIGN KEY (physician_user_id) REFERENCES users(user_id)
    ON UPDATE RESTRICT ON DELETE RESTRICT,
  CONSTRAINT fk_appointments_requested_by_user_id
    FOREIGN KEY (requested_by_user_id) REFERENCES users(user_id)
    ON UPDATE RESTRICT ON DELETE RESTRICT,
  CONSTRAINT fk_appointments_approved_by_user_id
    FOREIGN KEY (approved_by_user_id) REFERENCES users(user_id)
    ON UPDATE RESTRICT ON DELETE SET NULL,
  CONSTRAINT fk_appointments_consultation_type_id
    FOREIGN KEY (consultation_type_id) REFERENCES lookup_consultation_types(consultation_type_id)
    ON UPDATE RESTRICT ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE visits (
  visit_id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  patient_profile_id BIGINT UNSIGNED NOT NULL,
  physician_user_id BIGINT UNSIGNED NOT NULL,
  consultation_type_id BIGINT UNSIGNED NOT NULL,
  source_appointment_id BIGINT UNSIGNED NULL,
  arrival_time DATETIME NOT NULL,
  triage_level_id BIGINT UNSIGNED NULL,
  visit_status ENUM('queued','in_progress','completed') NOT NULL DEFAULT 'queued',
  created_by_user_id BIGINT UNSIGNED NOT NULL,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (visit_id),
  KEY idx_visits_patient_profile_id (patient_profile_id),
  KEY idx_visits_physician_status_arrival (physician_user_id, visit_status, arrival_time),
  KEY idx_visits_triage_arrival (triage_level_id, arrival_time),
  UNIQUE KEY uq_visits_source_appointment_id (source_appointment_id),
  KEY idx_visits_consultation_type_id (consultation_type_id),
  CONSTRAINT fk_visits_patient_profile_id
    FOREIGN KEY (patient_profile_id) REFERENCES patient_profiles(patient_profile_id)
    ON UPDATE RESTRICT ON DELETE RESTRICT,
  CONSTRAINT fk_visits_physician_user_id
    FOREIGN KEY (physician_user_id) REFERENCES users(user_id)
    ON UPDATE RESTRICT ON DELETE RESTRICT,
  CONSTRAINT fk_visits_consultation_type_id
    FOREIGN KEY (consultation_type_id) REFERENCES lookup_consultation_types(consultation_type_id)
    ON UPDATE RESTRICT ON DELETE RESTRICT,
  CONSTRAINT fk_visits_source_appointment_id
    FOREIGN KEY (source_appointment_id) REFERENCES appointments(appointment_id)
    ON UPDATE RESTRICT ON DELETE SET NULL,
  CONSTRAINT fk_visits_triage_level_id
    FOREIGN KEY (triage_level_id) REFERENCES lookup_triage_levels(triage_level_id)
    ON UPDATE RESTRICT ON DELETE SET NULL,
  CONSTRAINT fk_visits_created_by_user_id
    FOREIGN KEY (created_by_user_id) REFERENCES users(user_id)
    ON UPDATE RESTRICT ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 0-or-1 per visit enforced via UNIQUE(visit_id)
CREATE TABLE triage_records (
  triage_id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  visit_id BIGINT UNSIGNED NOT NULL,
  bp VARCHAR(20) NULL,
  heart_rate INT NULL,
  respiratory_rate INT NULL,
  temperature DECIMAL(4,1) NULL,
  oxygen_saturation INT NULL,
  weight DECIMAL(6,2) NULL,
  initial_assessment TEXT NULL,
  immediate_action TEXT NULL,
  referral_details TEXT NULL,
  emergency_contact_notified TINYINT(1) NULL,
  emergency_contact_notified_at DATETIME NULL,
  notes TEXT NULL,
  PRIMARY KEY (triage_id),
  UNIQUE KEY uq_triage_records_visit_id (visit_id),
  CONSTRAINT fk_triage_records_visit_id
    FOREIGN KEY (visit_id) REFERENCES visits(visit_id)
    ON UPDATE RESTRICT ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 0-or-1 per visit enforced via UNIQUE(visit_id)
CREATE TABLE consultations (
  consultation_id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  visit_id BIGINT UNSIGNED NOT NULL,
  history TEXT NULL,
  physical_exam TEXT NULL,
  assessment TEXT NULL,
  `plan` TEXT NULL,
  follow_up_instructions TEXT NULL,
  created_by_physician_id BIGINT UNSIGNED NOT NULL,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (consultation_id),
  UNIQUE KEY uq_consultations_visit_id (visit_id),
  KEY idx_consultations_created_by_physician_id (created_by_physician_id),
  CONSTRAINT fk_consultations_visit_id
    FOREIGN KEY (visit_id) REFERENCES visits(visit_id)
    ON UPDATE RESTRICT ON DELETE CASCADE,
  CONSTRAINT fk_consultations_created_by_physician_id
    FOREIGN KEY (created_by_physician_id) REFERENCES users(user_id)
    ON UPDATE RESTRICT ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE audit_logs (
  audit_log_id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  user_id BIGINT UNSIGNED NOT NULL,
  action_type VARCHAR(100) NOT NULL,
  entity_type VARCHAR(100) NOT NULL,
  entity_id BIGINT UNSIGNED NULL,
  description TEXT NULL,
  performed_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  ip_address VARCHAR(45) NULL,
  PRIMARY KEY (audit_log_id),
  KEY idx_audit_logs_user_id_performed_at (user_id, performed_at),
  KEY idx_audit_logs_entity (entity_type, entity_id),
  CONSTRAINT fk_audit_logs_user_id
    FOREIGN KEY (user_id) REFERENCES users(user_id)
    ON UPDATE RESTRICT ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- -----------------------------
-- Optional tables (create after required ones)
-- -----------------------------

-- Optional: physician_profiles (1-to-1 with users)
CREATE TABLE physician_profiles (
  physician_profile_id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  user_id BIGINT UNSIGNED NOT NULL,
  specialty VARCHAR(150) NULL,
  room VARCHAR(50) NULL,
  schedule_notes TEXT NULL,
  PRIMARY KEY (physician_profile_id),
  UNIQUE KEY uq_physician_profiles_user_id (user_id),
  CONSTRAINT fk_physician_profiles_user_id
    FOREIGN KEY (user_id) REFERENCES users(user_id)
    ON UPDATE RESTRICT ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;