// Attach CSRF token to every POST form so server-side CSRF validation can run globally.
window.formatDisplayLabel = (value) => {
	const overrides = {
		configuration_updated: "Configuration Updated",
		user_created: "User Created",
		user_updated: "User Updated",
		lookup_created: "Lookup Added",
		lookup_updated: "Lookup Updated",
		login: "Login",
		failed_login: "Failed Login",
		system_settings: "System Settings",
		users: "Users",
		sessions: "Sessions",
		lookups: "Lookups",
		appointments: "Appointments",
		consultations: "Consultations",
		reports: "Reports",
		clinic_admin: "Clinic Admin",
		system_admin: "System Admin",
		clinic_nurse: "Clinic Nurse",
		patient_user: "Patient User",
	};

	if (value === null || value === undefined) {
		return "-";
	}

	const text = String(value).trim();
	if (!text) {
		return "-";
	}

	const lookupKey = text.toLowerCase();
	if (Object.prototype.hasOwnProperty.call(overrides, lookupKey)) {
		return overrides[lookupKey];
	}

	return text.replace(/[_-]+/g, " ").replace(/\b\w/g, (letter) => letter.toUpperCase());
};

document.addEventListener("DOMContentLoaded", () => {
	document.querySelectorAll(".js-logo-fallback").forEach((logo) => {
		const jpgFallbackSrc = logo.getAttribute("data-logo-jpg");

		const showFallback = () => {
			logo.style.display = "none";
			const fallbackMark = logo.nextElementSibling;
			if (fallbackMark && fallbackMark.classList.contains("landing-brand-mark-fallback")) {
				fallbackMark.style.display = "inline-flex";
			}
		};

		const tryNextSourceOrFallback = () => {
			if (!logo.dataset.triedJpg && jpgFallbackSrc) {
				logo.dataset.triedJpg = "1";
				logo.src = jpgFallbackSrc;
				return;
			}
			showFallback();
		};

		logo.addEventListener("error", tryNextSourceOrFallback);

		if (logo.complete && logo.naturalWidth === 0) {
			tryNextSourceOrFallback();
		}
	});

	const token = document.querySelector('meta[name="csrf-token"]')?.getAttribute("content");
	if (!token) {
		return;
	}

	const forms = document.querySelectorAll("form");
	forms.forEach((form) => {
		const method = (form.getAttribute("method") || "get").toLowerCase();
		if (method !== "post") {
			return;
		}

		let hidden = form.querySelector('input[name="csrf_token"]');
		if (!hidden) {
			hidden = document.createElement("input");
			hidden.type = "hidden";
			hidden.name = "csrf_token";
			form.appendChild(hidden);
		}
		hidden.value = token;
	});

	const smoothScrollToTarget = (targetSelector) => {
		if (!targetSelector || !targetSelector.startsWith("#")) {
			return;
		}
		const target = document.querySelector(targetSelector);
		if (!target) {
			return;
		}

		target.scrollIntoView({
			behavior: "smooth",
			block: "start",
		});
	};

	document.querySelectorAll("[data-scroll-target]").forEach((link) => {
		link.addEventListener("click", (event) => {
			event.preventDefault();
			smoothScrollToTarget(link.getAttribute("data-scroll-target"));
		});
	});

	document.querySelectorAll('a[href^="#"]').forEach((anchor) => {
		anchor.addEventListener("click", (event) => {
			const href = anchor.getAttribute("href");
			if (!href || href.length <= 1) {
				return;
			}
			event.preventDefault();
			smoothScrollToTarget(href);
		});
	});

	document.querySelectorAll(".js-toggle-password").forEach((toggleButton) => {
		toggleButton.addEventListener("click", () => {
			const targetId = toggleButton.getAttribute("data-target-input");
			const input = targetId ? document.getElementById(targetId) : null;
			if (!input) {
				return;
			}

			const isPasswordType = input.getAttribute("type") === "password";
			input.setAttribute("type", isPasswordType ? "text" : "password");

			const icon = toggleButton.querySelector("i");
			if (icon) {
				icon.classList.toggle("bi-eye-fill", !isPasswordType);
				icon.classList.toggle("bi-eye-slash-fill", isPasswordType);
			}

			toggleButton.setAttribute("aria-label", isPasswordType ? "Hide password" : "Show password");
		});
	});

	const resendBtn = document.getElementById("resend_btn");
	if (resendBtn) {
		resendBtn.addEventListener("click", (e) => {
			const cooldownSeconds = parseInt(resendBtn.getAttribute("data-cooldown") || "60", 10);
			resendBtn.disabled = true;
			let remaining = cooldownSeconds;

			const updateButton = () => {
				resendBtn.textContent = `Resend in ${remaining}s`;
				remaining--;

				if (remaining < 0) {
					clearInterval(interval);
					resendBtn.disabled = false;
					resendBtn.textContent = "Resend code";
				}
			};

			updateButton();
			const interval = setInterval(updateButton, 1000);
		});
	}
});
