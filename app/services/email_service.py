"""Email delivery helpers."""

from __future__ import annotations

import smtplib
from email.message import EmailMessage

from flask import current_app


def _mail_enabled() -> bool:
	return bool(current_app.config.get("MAIL_ENABLED", False))


def _from_header() -> str:
	from_name = (current_app.config.get("MAIL_FROM_NAME") or current_app.config.get("APP_NAME") or "BatStateU CliniCare").strip()
	from_address = (current_app.config.get("MAIL_FROM_ADDRESS") or "").strip()
	if not from_address:
		return from_name
	return f"{from_name} <{from_address}>"


def send_verification_email(recipient_email: str, otp_code: str) -> bool:
	"""Send account verification email with OTP code.

	Returns True when email is sent successfully.
	Returns False when sending is skipped or fails.
	"""
	if not _mail_enabled():
		current_app.logger.info("MAIL_ENABLED is false. Skipping verification email send.")
		return False

	host = (current_app.config.get("MAIL_HOST") or "").strip()
	port = int(current_app.config.get("MAIL_PORT", 587))
	username = (current_app.config.get("MAIL_USERNAME") or "").strip()
	password = current_app.config.get("MAIL_PASSWORD") or ""
	use_tls = bool(current_app.config.get("MAIL_USE_TLS", True))
	use_ssl = bool(current_app.config.get("MAIL_USE_SSL", False))
	timeout_seconds = int(current_app.config.get("MAIL_TIMEOUT", 15))

	if not host:
		current_app.logger.warning("MAIL_HOST is not set. Cannot send verification email.")
		return False

	message = EmailMessage()
	message["Subject"] = "Verify your BatStateU CliniCare account"
	message["From"] = _from_header()
	message["To"] = recipient_email
	
	html_content = f"""
	<html>
		<head>
			<meta charset="utf-8">
			<meta name="viewport" content="width=device-width, initial-scale=1.0">
			<style>
				body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; line-height: 1.6; color: #333; }}
				.email-container {{ max-width: 600px; margin: 0 auto; background: #fafafa; }}
				.email-header {{ background: linear-gradient(130deg, #a91321, #d91f2d); padding: 2rem; text-align: center; color: white; }}
				.email-logo {{ font-size: 1.8rem; font-weight: 700; margin-bottom: 0.5rem; }}
				.email-subtitle {{ font-size: 0.95rem; opacity: 0.9; }}
				.email-body {{ padding: 2rem; background: white; }}
				.email-section {{ margin-bottom: 2rem; }}
				.email-greeting {{ font-size: 1.1rem; font-weight: 600; color: #3c2730; margin-bottom: 1rem; }}
				.email-text {{ color: #666; margin-bottom: 1rem; }}
				.otp-container {{ background: #f5f5f5; border: 2px solid #e0e0e0; border-radius: 12px; padding: 1.5rem; text-align: center; margin: 2rem 0; }}
				.otp-label {{ font-size: 0.9rem; color: #999; text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 0.5rem; }}
				.otp-code {{ font-size: 2.5rem; font-weight: 700; color: #d91f2d; letter-spacing: 0.2em; font-family: 'Courier New', monospace; }}
				.email-footer {{ background: #f9f9f9; border-top: 1px solid #e0e0e0; padding: 1.5rem; text-align: center; font-size: 0.85rem; color: #999; }}
				.email-accent {{ color: #d91f2d; font-weight: 600; }}
			</style>
		</head>
		<body>
			<div class="email-container">
				<div class="email-header">
					<div class="email-logo">BatStateU CliniCare</div>
					<div class="email-subtitle">Batangas State University - Lipa Campus</div>
				</div>
				
				<div class="email-body">
					<div class="email-section">
						<div class="email-greeting">Hi there!</div>
						<div class="email-text">Thank you for registering with <span class="email-accent">BatStateU CliniCare</span>. We're excited to have you on board!</div>
					</div>
					
					<div class="email-section">
						<div class="email-text">To verify your account, please use the code below:</div>
						
						<div class="otp-container">
							<div class="otp-label">Your Verification Code</div>
							<div class="otp-code">{otp_code}</div>
						</div>
						
						<div class="email-text">Enter this code on the verification screen to complete your registration.</div>
						<div class="email-text" style="color: #999; font-size: 0.9rem;">⏱️ This code expires in <span class="email-accent">24 hours</span></div>
					</div>
					
					<div class="email-section" style="border-top: 1px solid #f0f0f0; padding-top: 1.5rem; margin-top: 2rem;">
						<div class="email-text" style="font-size: 0.9rem; color: #999;">
							If you did not request this verification code, please disregard this email. No action is required.
						</div>
					</div>
				</div>
				
				<div class="email-footer">
					<div>BatStateU CliniCare • Lipa Campus</div>
					<div style="margin-top: 0.5rem; color: #bbb;">© 2026 Batangas State University. All rights reserved.</div>
				</div>
			</div>
		</body>
	</html>
	"""
	
	message.set_content(
		"\n".join(
			[
				"Hi,",
				"",
				"Thank you for registering with BatStateU CliniCare.",
				"Please verify your account using this code:",
				"",
				f"  {otp_code}",
				"",
				"Enter this code on the verification screen. The code expires in 24 hours.",
				"",
				"If you did not request this, you may ignore this email.",
			]
		)
	)
	message.add_alternative(html_content, subtype="html")

	try:
		if use_ssl:
			with smtplib.SMTP_SSL(host=host, port=port, timeout=timeout_seconds) as smtp:
				if username:
					smtp.login(username, password)
				smtp.send_message(message)
		else:
			with smtplib.SMTP(host=host, port=port, timeout=timeout_seconds) as smtp:
				if use_tls:
					smtp.starttls()
				if username:
					smtp.login(username, password)
				smtp.send_message(message)
	except Exception:
		current_app.logger.exception("Failed to send verification email to %s", recipient_email)
		return False

	current_app.logger.info("Verification email sent to %s", recipient_email)
	return True
