# Marburg Repair Hub — Flask + SQLite

A repair-location finder for Marburg, converted from a static site to a full
Flask application with an SQLite database and Jinja2 templates.

## Run

```bash
pip install -r requirements.txt
python app.py
```

Open http://127.0.0.1:5000/

The database (`repair_hub.db`) is created and seeded automatically on first run.

## Admin panel

- URL: http://127.0.0.1:5000/admin  (only reachable via `/admin`)
- Password: `12344`

From the admin panel you can:
- Update the **receiver email** used by the Contact form (and public phone).
- **Add / remove FAQs** (bilingual EN/DE) shown on the FAQ page.
- **Add / remove cafés** shown on the home page, choosing which services each offers.

## Features

1. **Multilingual** — English + German. Toggle with the `EN / DE` switch in the
   header (stored in the session). UI copy, About, FAQs and service names are
   translated.
2. **Default café list** — the map sidebar shows all cafés before any search/filter.
3. **Navigation** — "Events" and "Become a Partner" removed.
4. **Admin at `/admin`** — not linked in the menu.
5. **Password protection** — simple login form (password `12344`).
6. **Email configuration** — editable receiver email in admin.
7. **FAQ management** — add/remove from admin.
8. **Café management** — add/remove from admin.
9. **Services (many-to-many)** — `cafes` ↔ `services` via `cafe_services`.
   Clicking a service category on the home page filters cafés to that service.
10. **Search** — the sidebar search filters cafés live by name or service
    (matches English and German service names). The hero search box feeds the
    same filter.

## Project structure

```
marburg/
├── app.py              # Flask app, routes, i18n strings, DB seed
├── schema.sql          # SQLite schema
├── requirements.txt
├── repair_hub.db       # auto-created on first run
├── static/
│   ├── style.css
│   ├── script.js       # map + search + service filtering
│   └── images/         # put logo.png, favicon.png, category images here
└── templates/
    ├── base.html       # shared header / nav / footer
    ├── index.html
    ├── about.html
    ├── contact.html
    ├── faq.html
    ├── admin_login.html
    └── admin.html
```

## Notes

- Place your existing image assets (`logo.png`, `favicon.png`, `phone.jpg`,
  `laptop.jpg`, `1985.jpg`, etc.) into `static/images/` to restore the visuals.
- Contact submissions are stored in the `messages` table. Wiring up real email
  delivery (SMTP) is the only remaining step — the configured receiver address
  is read from settings in the `/contact` handler.
- Change `app.secret_key` and move `ADMIN_PASSWORD` to an environment variable
  before deploying.
