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

	const appointmentForm = document.getElementById("appointment-request-form");
	if (appointmentForm) {
		const dateInput = appointmentForm.querySelector("#scheduled_date");
		const timeInput = appointmentForm.querySelector("#scheduled_time");
		const clearDateValidity = () => {
			if (dateInput) {
				dateInput.setCustomValidity("");
			}
		};

		if (dateInput) {
			dateInput.addEventListener("input", clearDateValidity);
			dateInput.addEventListener("change", clearDateValidity);
		}

		appointmentForm.addEventListener("submit", (event) => {
			if (!dateInput || !timeInput) {
				return;
			}

			const dateValue = dateInput.value;
			const timeValue = timeInput.value;

			if (!dateValue && !timeValue) {
				return;
			}

			if (!dateValue || !timeValue) {
				event.preventDefault();
				dateInput.setCustomValidity("Please provide both a preferred date and time.");
				dateInput.reportValidity();
				return;
			}

			const dateParts = dateValue.split("-");
			if (dateParts.length !== 3) {
				event.preventDefault();
				dateInput.setCustomValidity("Preferred date is invalid.");
				dateInput.reportValidity();
				return;
			}

			const scheduleDate = new Date(`${dateValue}T00:00:00`);
			const day = scheduleDate.getDay();
			if (day === 0 || day === 6) {
				event.preventDefault();
				dateInput.setCustomValidity("Clinic is closed on weekends. Please select a weekday.");
				dateInput.reportValidity();
				return;
			}

			const timeParts = timeValue.split(":");
			const hour = parseInt(timeParts[0] || "0", 10);
			const minute = parseInt(timeParts[1] || "0", 10);
			if (Number.isNaN(hour) || Number.isNaN(minute)) {
				event.preventDefault();
				dateInput.setCustomValidity("Preferred time is invalid.");
				dateInput.reportValidity();
				return;
			}

			const minutesSinceMidnight = hour * 60 + minute;
			const openMinutes = 8 * 60;
			const closeMinutes = 17 * 60;
			if (minutesSinceMidnight < openMinutes || minutesSinceMidnight >= closeMinutes) {
				event.preventDefault();
				dateInput.setCustomValidity("Clinic hours are Mon - Fri, 8:00 AM to 5:00 PM.");
				dateInput.reportValidity();
				return;
			}

			dateInput.setCustomValidity("");
		});
	}

		const landingNav = document.querySelector(".clinic-landing-header");
		if (landingNav) {
			const navLinks = Array.from(landingNav.querySelectorAll('.nav-link[href^="#"]'));
			const navTargets = navLinks
				.map((link) => {
					const href = link.getAttribute("href");
					if (!href || href.length <= 1) {
						return null;
					}
					const target = document.querySelector(href);
					return target ? { link, target } : null;
				})
				.filter(Boolean);

			if (navTargets.length > 0) {
				const setActiveLink = (activeLink) => {
					navLinks.forEach((link) => link.classList.toggle("active", link === activeLink));
				};
				let manualActiveLink = null;
				let manualActiveUntil = 0;

				const updateActiveLink = () => {
					if (manualActiveLink && Date.now() < manualActiveUntil) {
						setActiveLink(manualActiveLink);
						return;
					}
					manualActiveLink = null;
					const headerOffset = landingNav.offsetHeight + 16;
					let current = navTargets[0].link;

					for (const { link, target } of navTargets) {
						const top = target.getBoundingClientRect().top - headerOffset;
						if (top <= 0) {
							current = link;
						} else {
							break;
						}
					}

					setActiveLink(current);
				};

				navLinks.forEach((link) => {
					link.addEventListener("click", () => {
						manualActiveLink = link;
						manualActiveUntil = Date.now() + 900;
						setActiveLink(link);
					});
				});

				updateActiveLink();
				window.addEventListener("scroll", updateActiveLink, { passive: true });
				window.addEventListener("resize", updateActiveLink);
			}
		}
});
