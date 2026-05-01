-- BatStateU CliniCare Stored Procedures + Triggers (MySQL 8.x)
-- Uses the existing schema exactly (no table/column changes).
-- Run AFTER batstateu_clinicare_schema.sql (and optional tables if you will use them).

-- For re-runs during development
-- (You can comment these out if your MySQL version/permissions disallow it.)

DELIMITER $$
-- -----------------------------
-- 1) Audit logging helper (REQUIRED)
-- -----------------------------
DROP PROCEDURE IF EXISTS sp_audit_log $$
CREATE PROCEDURE sp_audit_log(
  IN p_user_id BIGINT UNSIGNED,
  IN p_action_type VARCHAR(100),
  IN p_entity_type VARCHAR(100),
  IN p_entity_id BIGINT UNSIGNED,
  IN p_description TEXT,
  IN p_ip_address VARCHAR(45)
)
BEGIN
  INSERT INTO audit_logs (user_id, action_type, entity_type, entity_id, description, performed_at, ip_address)
  VALUES (p_user_id, p_action_type, p_entity_type, p_entity_id, p_description, UTC_TIMESTAMP(), p_ip_address);
END $$

-- -----------------------------
-- 2) User activation after email verification (REQUIRED)
-- -----------------------------
DROP PROCEDURE IF EXISTS sp_activate_user_after_verification $$
CREATE PROCEDURE sp_activate_user_after_verification(
  IN p_token VARCHAR(255),
  IN p_ip_address VARCHAR(45)
)
BEGIN
  DECLARE v_user_id BIGINT UNSIGNED;
  DECLARE v_expires_at DATETIME;
  DECLARE v_verified_at DATETIME;
  DECLARE v_not_found TINYINT(1) DEFAULT 0;

  DECLARE EXIT HANDLER FOR SQLEXCEPTION
  BEGIN
    ROLLBACK;
    RESIGNAL;
  END;

  DECLARE CONTINUE HANDLER FOR NOT FOUND SET v_not_found = 1;

  START TRANSACTION;

  SELECT ev.user_id, ev.expires_at, ev.verified_at
    INTO v_user_id, v_expires_at, v_verified_at
  FROM email_verifications ev
  WHERE ev.token = p_token
  LIMIT 1
  FOR UPDATE;

  IF v_not_found = 1 OR v_user_id IS NULL THEN
    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Invalid verification token.';
  END IF;

  IF v_verified_at IS NOT NULL THEN
    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Token already used.';
  END IF;

  IF v_expires_at < UTC_TIMESTAMP() THEN
    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Verification token expired.';
  END IF;

  UPDATE email_verifications
  SET verified_at = UTC_TIMESTAMP()
  WHERE token = p_token;

  UPDATE users
  SET account_status = 'active'
  WHERE user_id = v_user_id;

  CALL sp_audit_log(v_user_id, 'account_activated', 'users', v_user_id,
                   'User account activated after email verification.', p_ip_address);

  COMMIT;

  -- Return the activated user_id
  SELECT v_user_id AS user_id;
END $$

-- -----------------------------
-- 3) Appointment request creation (REQUIRED)
-- -----------------------------
DROP PROCEDURE IF EXISTS sp_create_appointment_request $$
CREATE PROCEDURE sp_create_appointment_request(
  IN p_patient_profile_id BIGINT UNSIGNED,
  IN p_physician_user_id BIGINT UNSIGNED,
  IN p_requested_by_user_id BIGINT UNSIGNED,
  IN p_consultation_type_id BIGINT UNSIGNED,
  IN p_scheduled_date DATE,
  IN p_scheduled_time TIME,
  IN p_reason VARCHAR(255),
  IN p_ip_address VARCHAR(45)
)
BEGIN
  DECLARE v_appointment_id BIGINT UNSIGNED;

  -- Simple validation: scheduled date/time can be NULL for "request only"
  IF p_scheduled_date IS NOT NULL AND p_scheduled_date < CURDATE() THEN
    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Scheduled date cannot be in the past.';
  END IF;

  INSERT INTO appointments (
    patient_profile_id,
    physician_user_id,
    requested_by_user_id,
    scheduled_date,
    scheduled_time,
    reason,
    consultation_type_id,
    status,
    approved_by_user_id
  ) VALUES (
    p_patient_profile_id,
    p_physician_user_id,
    p_requested_by_user_id,
    p_scheduled_date,
    p_scheduled_time,
    p_reason,
    p_consultation_type_id,
    'pending',
    NULL
  );

  SET v_appointment_id = LAST_INSERT_ID();

  CALL sp_audit_log(p_requested_by_user_id, 'appointment_requested', 'appointments', v_appointment_id,
                   CONCAT('Appointment requested. Status=pending. Physician user_id=', p_physician_user_id), p_ip_address);

  SELECT v_appointment_id AS appointment_id;
END $$

-- -----------------------------
-- 4) Appointment approval or adjustment (REQUIRED)
-- -----------------------------
DROP PROCEDURE IF EXISTS sp_approve_or_adjust_appointment $$
CREATE PROCEDURE sp_approve_or_adjust_appointment(
  IN p_appointment_id BIGINT UNSIGNED,
  IN p_approved_by_user_id BIGINT UNSIGNED,
  IN p_new_physician_user_id BIGINT UNSIGNED,
  IN p_new_scheduled_date DATE,
  IN p_new_scheduled_time TIME,
  IN p_new_status VARCHAR(20),
  IN p_ip_address VARCHAR(45)
)
BEGIN
  DECLARE v_old_status VARCHAR(20);
  DECLARE v_new_status VARCHAR(20);
  DECLARE v_current_physician_user_id BIGINT UNSIGNED;
  DECLARE v_current_scheduled_date DATE;
  DECLARE v_current_scheduled_time TIME;
  DECLARE v_effective_physician_user_id BIGINT UNSIGNED;
  DECLARE v_effective_scheduled_date DATE;
  DECLARE v_effective_scheduled_time TIME;
  DECLARE v_conflict_appointment_id BIGINT UNSIGNED;
  DECLARE v_slot_lock_name VARCHAR(128);
  DECLARE v_lock_acquired INT DEFAULT 0;
  DECLARE v_not_found TINYINT(1) DEFAULT 0;

  DECLARE EXIT HANDLER FOR SQLEXCEPTION
  BEGIN
    ROLLBACK;
    IF v_lock_acquired = 1 THEN
      DO RELEASE_LOCK(v_slot_lock_name);
    END IF;
    RESIGNAL;
  END;

  DECLARE CONTINUE HANDLER FOR NOT FOUND SET v_not_found = 1;

  START TRANSACTION;

  SELECT status, physician_user_id, scheduled_date, scheduled_time
    INTO v_old_status, v_current_physician_user_id, v_current_scheduled_date, v_current_scheduled_time
  FROM appointments
  WHERE appointment_id = p_appointment_id
  LIMIT 1
  FOR UPDATE;

  IF v_not_found = 1 OR v_old_status IS NULL THEN
    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Appointment not found.';
  END IF;

  -- Basic allowed transitions
  IF v_old_status IN ('completed','cancelled','no_show') THEN
    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Appointment is already closed; cannot modify.';
  END IF;

  IF p_new_scheduled_date IS NOT NULL AND p_new_scheduled_date < CURDATE() THEN
    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Scheduled date cannot be in the past.';
  END IF;

  SET v_new_status = COALESCE(p_new_status, v_old_status);
  IF v_new_status NOT IN ('pending','approved','checked_in','completed','cancelled','no_show') THEN
    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Invalid appointment status.';
  END IF;

  -- Effective slot values after applying COALESCE updates
  SET v_effective_physician_user_id = COALESCE(p_new_physician_user_id, v_current_physician_user_id);
  SET v_effective_scheduled_date = COALESCE(p_new_scheduled_date, v_current_scheduled_date);
  SET v_effective_scheduled_time = COALESCE(p_new_scheduled_time, v_current_scheduled_time);

  -- Conflict prevention: when an appointment is approved/checked_in, it must have a time slot
  -- and the physician cannot already have another approved/checked_in appointment at the same slot.
  IF v_new_status IN ('approved','checked_in') THEN
    IF v_effective_physician_user_id IS NULL OR v_effective_scheduled_date IS NULL OR v_effective_scheduled_time IS NULL THEN
      SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Approved/checked-in appointments must have physician, date, and time.';
    END IF;

    -- Named lock avoids two simultaneous approvals booking the same slot.
    SET v_slot_lock_name = CONCAT('appt_slot_', v_effective_physician_user_id, '_', v_effective_scheduled_date, '_', v_effective_scheduled_time);
    SELECT GET_LOCK(v_slot_lock_name, 5) INTO v_lock_acquired;
    IF v_lock_acquired <> 1 THEN
      SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Could not lock appointment slot; please retry.';
    END IF;

    SET v_conflict_appointment_id = NULL;
    SELECT a.appointment_id
      INTO v_conflict_appointment_id
    FROM appointments a
    WHERE a.physician_user_id = v_effective_physician_user_id
      AND a.scheduled_date = v_effective_scheduled_date
      AND a.scheduled_time = v_effective_scheduled_time
      AND a.status IN ('approved','checked_in')
      AND a.appointment_id <> p_appointment_id
    LIMIT 1
    FOR UPDATE;

    IF v_conflict_appointment_id IS NOT NULL THEN
      SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Physician already has an appointment at that date/time.';
    END IF;
  END IF;

  UPDATE appointments
  SET
    physician_user_id = COALESCE(p_new_physician_user_id, physician_user_id),
    scheduled_date = COALESCE(p_new_scheduled_date, scheduled_date),
    scheduled_time = COALESCE(p_new_scheduled_time, scheduled_time),
    status = v_new_status,
    approved_by_user_id = p_approved_by_user_id
  WHERE appointment_id = p_appointment_id;

  CALL sp_audit_log(p_approved_by_user_id, 'appointment_updated', 'appointments', p_appointment_id,
                   CONCAT('Appointment updated. Old status=', v_old_status, ', New status=', v_new_status),
                   p_ip_address);

  COMMIT;

  IF v_lock_acquired = 1 THEN
    DO RELEASE_LOCK(v_slot_lock_name);
  END IF;

  SELECT p_appointment_id AS appointment_id;
END $$

-- -----------------------------
-- 5) Check-in an approved appointment (REQUIRED)
-- -----------------------------
DROP PROCEDURE IF EXISTS sp_check_in_appointment $$
CREATE PROCEDURE sp_check_in_appointment(
  IN p_appointment_id BIGINT UNSIGNED,
  IN p_checked_in_by_user_id BIGINT UNSIGNED,
  IN p_ip_address VARCHAR(45)
)
BEGIN
  DECLARE v_status VARCHAR(20);
  DECLARE v_not_found TINYINT(1) DEFAULT 0;

  DECLARE EXIT HANDLER FOR SQLEXCEPTION
  BEGIN
    ROLLBACK;
    RESIGNAL;
  END;

  DECLARE CONTINUE HANDLER FOR NOT FOUND SET v_not_found = 1;

  START TRANSACTION;

  SELECT status INTO v_status
  FROM appointments
  WHERE appointment_id = p_appointment_id
  LIMIT 1
  FOR UPDATE;

  IF v_not_found = 1 OR v_status IS NULL THEN
    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Appointment not found.';
  END IF;

  IF v_status <> 'approved' THEN
    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Only approved appointments can be checked in.';
  END IF;

  UPDATE appointments
  SET status = 'checked_in'
  WHERE appointment_id = p_appointment_id;

  CALL sp_audit_log(p_checked_in_by_user_id, 'appointment_checked_in', 'appointments', p_appointment_id,
                   'Appointment checked in.', p_ip_address);

  COMMIT;

  SELECT p_appointment_id AS appointment_id;
END $$

-- -----------------------------
-- 6) Visit creation from a checked-in appointment (REQUIRED)
-- -----------------------------
DROP PROCEDURE IF EXISTS sp_create_visit_from_checked_in_appointment $$
CREATE PROCEDURE sp_create_visit_from_checked_in_appointment(
  IN p_appointment_id BIGINT UNSIGNED,
  IN p_created_by_user_id BIGINT UNSIGNED,
  IN p_arrival_time DATETIME,
  IN p_ip_address VARCHAR(45)
)
BEGIN
  DECLARE v_patient_profile_id BIGINT UNSIGNED;
  DECLARE v_physician_user_id BIGINT UNSIGNED;
  DECLARE v_consultation_type_id BIGINT UNSIGNED;
  DECLARE v_status VARCHAR(20);
  DECLARE v_visit_id BIGINT UNSIGNED;
  DECLARE v_existing_visit_id BIGINT UNSIGNED;
  DECLARE v_appt_lock_name VARCHAR(128);
  DECLARE v_lock_acquired INT DEFAULT 0;
  DECLARE v_not_found TINYINT(1) DEFAULT 0;

  DECLARE EXIT HANDLER FOR SQLEXCEPTION
  BEGIN
    ROLLBACK;
    IF v_lock_acquired = 1 THEN
      DO RELEASE_LOCK(v_appt_lock_name);
    END IF;
    RESIGNAL;
  END;

  DECLARE CONTINUE HANDLER FOR NOT FOUND SET v_not_found = 1;

  START TRANSACTION;

  -- Named lock prevents two sessions creating multiple visits for the same appointment.
  SET v_appt_lock_name = CONCAT('visit_from_appt_', p_appointment_id);
  SELECT GET_LOCK(v_appt_lock_name, 5) INTO v_lock_acquired;
  IF v_lock_acquired <> 1 THEN
    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Could not lock appointment for visit creation; please retry.';
  END IF;

  SELECT patient_profile_id, physician_user_id, consultation_type_id, status
    INTO v_patient_profile_id, v_physician_user_id, v_consultation_type_id, v_status
  FROM appointments
  WHERE appointment_id = p_appointment_id
  LIMIT 1
  FOR UPDATE;

  IF v_not_found = 1 OR v_status IS NULL THEN
    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Appointment not found.';
  END IF;

  IF v_status <> 'checked_in' THEN
    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Appointment must be checked_in before creating a visit.';
  END IF;

  -- Enforce 0-or-1 visits per appointment (design rule)
  SET v_existing_visit_id = NULL;
  SELECT visit_id
    INTO v_existing_visit_id
  FROM visits
  WHERE source_appointment_id = p_appointment_id
  LIMIT 1
  FOR UPDATE;

  IF v_existing_visit_id IS NOT NULL THEN
    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'A visit already exists for this appointment.';
  END IF;

  INSERT INTO visits (
    patient_profile_id,
    physician_user_id,
    consultation_type_id,
    source_appointment_id,
    arrival_time,
    triage_level_id,
    visit_status,
    created_by_user_id
  ) VALUES (
    v_patient_profile_id,
    v_physician_user_id,
    v_consultation_type_id,
    p_appointment_id,
    COALESCE(p_arrival_time, UTC_TIMESTAMP()),
    NULL,
    'queued',
    p_created_by_user_id
  );

  SET v_visit_id = LAST_INSERT_ID();

  CALL sp_audit_log(p_created_by_user_id, 'visit_created_from_appointment', 'visits', v_visit_id,
                   CONCAT('Visit created from appointment_id=', p_appointment_id), p_ip_address);

  COMMIT;

  IF v_lock_acquired = 1 THEN
    DO RELEASE_LOCK(v_appt_lock_name);
  END IF;

  SELECT v_visit_id AS visit_id;
END $$

-- -----------------------------
-- 7) Walk-in or emergency visit creation (REQUIRED)
-- -----------------------------
DROP PROCEDURE IF EXISTS sp_create_walkin_or_emergency_visit $$
CREATE PROCEDURE sp_create_walkin_or_emergency_visit(
  IN p_patient_profile_id BIGINT UNSIGNED,
  IN p_physician_user_id BIGINT UNSIGNED,
  IN p_consultation_type_id BIGINT UNSIGNED,
  IN p_triage_level_id BIGINT UNSIGNED,
  IN p_created_by_user_id BIGINT UNSIGNED,
  IN p_arrival_time DATETIME,
  IN p_ip_address VARCHAR(45)
)
BEGIN
  DECLARE v_visit_id BIGINT UNSIGNED;

  INSERT INTO visits (
    patient_profile_id,
    physician_user_id,
    consultation_type_id,
    source_appointment_id,
    arrival_time,
    triage_level_id,
    visit_status,
    created_by_user_id
  ) VALUES (
    p_patient_profile_id,
    p_physician_user_id,
    p_consultation_type_id,
    NULL,
    COALESCE(p_arrival_time, UTC_TIMESTAMP()),
    p_triage_level_id,
    'queued',
    p_created_by_user_id
  );

  SET v_visit_id = LAST_INSERT_ID();

  CALL sp_audit_log(p_created_by_user_id, 'visit_created_walkin_emergency', 'visits', v_visit_id,
                   'Walk-in/emergency visit created (no linked appointment).', p_ip_address);

  SELECT v_visit_id AS visit_id;
END $$


-- =====================================================================
-- TRIGGERS
-- =====================================================================

-- -----------------------------
-- A) Automatic visit completion when consultation is created (REQUIRED)
--    Assumption: inserting a consultation record means the consult is finished.
-- -----------------------------
DROP TRIGGER IF EXISTS trg_consultations_after_insert_complete_visit $$
CREATE TRIGGER trg_consultations_after_insert_complete_visit
AFTER INSERT ON consultations
FOR EACH ROW
BEGIN
  UPDATE visits
  SET visit_status = 'completed', updated_at = UTC_TIMESTAMP()
  WHERE visit_id = NEW.visit_id;

  -- Audit the completion (uses physician who created the consult)
  INSERT INTO audit_logs (user_id, action_type, entity_type, entity_id, description, performed_at, ip_address)
  VALUES (
    NEW.created_by_physician_id,
    'visit_completed',
    'visits',
    NEW.visit_id,
    'Visit marked completed after consultation was created.',
    UTC_TIMESTAMP(),
    NULL
  );
END $$

-- -----------------------------
-- B) Automatic appointment completion when linked visit is completed (REQUIRED)
-- -----------------------------
DROP TRIGGER IF EXISTS trg_visits_after_update_complete_appointment $$
CREATE TRIGGER trg_visits_after_update_complete_appointment
AFTER UPDATE ON visits
FOR EACH ROW
BEGIN
  IF NEW.visit_status = 'completed'
     AND OLD.visit_status <> 'completed'
     AND NEW.source_appointment_id IS NOT NULL THEN

    UPDATE appointments
    SET status = 'completed', updated_at = UTC_TIMESTAMP()
    WHERE appointment_id = NEW.source_appointment_id
      AND status IN ('approved','checked_in');

    -- Audit the appointment completion (uses the visit creator for linkage)
    INSERT INTO audit_logs (user_id, action_type, entity_type, entity_id, description, performed_at, ip_address)
    VALUES (
      NEW.created_by_user_id,
      'appointment_completed',
      'appointments',
      NEW.source_appointment_id,
      CONCAT('Appointment auto-completed when linked visit_id=', NEW.visit_id, ' completed.'),
      UTC_TIMESTAMP(),
      NULL
    );

  END IF;
END $$


DELIMITER ;

-- =====================================================================
-- SHORT EXPLANATION (as SQL comments)
-- =====================================================================
-- Stored Procedures:
-- - sp_audit_log: Inserts an audit log row (central helper).
-- - sp_activate_user_after_verification: Validates token, marks verified, activates user.
-- - sp_create_appointment_request: Inserts a pending appointment request.
-- - sp_approve_or_adjust_appointment: Approves/adjusts/cancels appointment with basic status rules.
-- - sp_check_in_appointment: Moves an approved appointment to checked_in.
-- - sp_create_visit_from_checked_in_appointment: Creates a visit linked to a checked-in appointment.
-- - sp_create_walkin_or_emergency_visit: Creates a visit with no appointment (walk-in/emergency).
--
-- Triggers:
-- - trg_consultations_after_insert_complete_visit (REQUIRED): Auto-marks the related visit as completed.
-- - trg_visits_after_update_complete_appointment (REQUIRED): Auto-completes appointment when linked visit completes.
--
-- Required vs Optional:
-- - REQUIRED: All procedures and triggers listed above.