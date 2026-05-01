# Implementation Notes
## BatStateU CliniCare — Starter Scaffold Checklist

This checklist is the minimum starter scaffold for the approved PHP + MySQL localhost prototype.

---

## A. First Files to Create per Folder

### public/
- [ ] `public/index.php`
- [ ] `public/.htaccess`
- [ ] `public/assets/css/app.css`
- [ ] `public/assets/js/app.js`

### app/config/
- [ ] `app/config/app.php`
- [ ] `app/config/database.php`
- [ ] `app/config/constants.php`

### app/core/
- [ ] `app/core/Router.php`
- [ ] `app/core/Controller.php`
- [ ] `app/core/View.php`
- [ ] `app/core/Session.php`
- [ ] `app/core/Auth.php`
- [ ] `app/core/Authorization.php`

### app/helpers/
- [ ] `app/helpers/functions.php`
- [ ] `app/helpers/validation.php`

### app/views/layouts/
- [ ] `app/views/layouts/main.php`
- [ ] `app/views/layouts/auth.php`

### app/views/shared/
- [ ] `app/views/shared/topbar.php`
- [ ] `app/views/shared/sidebar.php`
- [ ] `app/views/shared/flash_messages.php`

### app/views/auth/
- [ ] `app/views/auth/login.php`
- [ ] `app/views/auth/register.php`
- [ ] `app/views/auth/verify_notice.php`

### app/controllers/
- [ ] `app/controllers/HomeController.php`
- [ ] `app/controllers/AuthController.php`

### app/models/
- [ ] `app/models/User.php`
- [ ] `app/models/PatientProfile.php`

### storage/
- [ ] `storage/logs/.gitkeep`
- [ ] `storage/uploads/.gitkeep`

---

## B. Purpose of Each Starter Group

- `public/`: web entry + static assets
- `app/config/`: app/database configuration and constants
- `app/core/`: minimal MVC core + auth/session/authorization shell
- `app/helpers/`: common utility and validation helpers
- `app/views/layouts|shared/`: reusable page shell and partials
- `app/views/auth/`: initial auth screens
- `app/controllers/`: first runnable route handlers
- `app/models/`: initial DB entity wrappers
- `storage/`: runtime logs and upload placeholders

---

## C. Files That Should Have Starter Code Immediately

- `public/index.php`
- `public/.htaccess`
- `app/config/app.php`
- `app/config/database.php`
- `app/config/constants.php`
- `app/core/Router.php`
- `app/core/Controller.php`
- `app/core/View.php`
- `app/core/Session.php`
- `app/helpers/functions.php`
- `app/views/layouts/main.php`
- `app/views/shared/flash_messages.php`
- `app/controllers/HomeController.php`

---

## D. Files That Can Stay Empty Placeholders for Now

- `app/core/Auth.php`
- `app/core/Authorization.php`
- `app/helpers/validation.php`
- `app/views/layouts/auth.php`
- `app/views/shared/topbar.php`
- `app/views/shared/sidebar.php`
- `app/views/auth/login.php`
- `app/views/auth/register.php`
- `app/views/auth/verify_notice.php`
- `app/controllers/AuthController.php`
- `app/models/User.php`
- `app/models/PatientProfile.php`
- `public/assets/css/app.css`
- `public/assets/js/app.js`

---

## E. Recommended File Creation Order

1. Config files (`app.php`, `constants.php`, `database.php`)
2. Core files (`Router.php`, `Controller.php`, `View.php`, `Session.php`)
3. Helpers (`functions.php`)
4. Public bootstrap (`index.php`, `.htaccess`)
5. Layout + shared flash partial
6. `HomeController.php` + one starter home view
7. Placeholder auth/model files

---

## F. Minimum Bootstrap Files Required to Start Running

These are the minimum files needed so the project can run:

- `public/index.php`
- `public/.htaccess`
- `app/config/app.php`
- `app/config/database.php`
- `app/core/Router.php`
- `app/core/Controller.php`
- `app/core/View.php`
- `app/core/Session.php`
- `app/helpers/functions.php`
- `app/controllers/HomeController.php`
- `app/views/layouts/main.php`

---

## G. Scope Guard (Do Not Expand Yet)

- Do not add full module code yet.
- Keep `visits` as central workflow in later module implementation.
- Use approved schema + procedures/triggers only.
- Build role dashboards and core flows incrementally after bootstrap is stable.
