"""
Marburg Repair Hub — Flask backend
----------------------------------
Run:
    pip install -r requirements.txt
    python app.py
Then open http://127.0.0.1:5000/
Admin panel:  http://127.0.0.1:5000/admin   (password: 12344)
"""

import os
import sqlite3

from flask import (
    Flask, g, render_template, request, redirect, url_for,
    session, flash, abort, jsonify
)

# --------------------------------------------------------------------------- #
#  Configuration
# --------------------------------------------------------------------------- #
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DATABASE = os.path.join(BASE_DIR, "repair_hub.db")
SCHEMA = os.path.join(BASE_DIR, "schema.sql")

ADMIN_PASSWORD = "12344"          # hardcoded for now (requirement #5)
SUPPORTED_LANGS = ("en", "de")

app = Flask(__name__)
app.secret_key = "change-this-secret-key-in-production"


# --------------------------------------------------------------------------- #
#  UI translation strings (chrome / static copy)
# --------------------------------------------------------------------------- #
STRINGS = {
    "en": {
        "site_name": "Marburg Repair Help",
        # nav
        "nav_map": "Map", "nav_services": "Services", "nav_about": "About",
        "nav_contact": "Contact Us", "nav_faqs": "FAQs", 
        "nav_partner": "Become a Partner",
        "partner_coming_soon": "The 'Become a Partner' feature is currently under development and will be available in a future version of Marburg Repair Hub.",
        # hero
        "hero_title": "Repair Instead of Replace",
        "hero_sub": "Find repair services in Marburg and reduce electronic waste.",
        "search_placeholder": "What do you want to repair?",
        "search_btn": "Search",
        # categories
        "categories_title": "Popular Repair Categories",
        # co2
        "co2_title": "🌱 Environmental Impact",
        # map
        "map_title": "Repair Locations in Marburg",
        "sidebar_search": "Search repair cafés or device type...",
        "all_services": "All services",
        "no_results": "No matching locations found.",
        "clear_filter": "Show all",
        # detail labels
        "d_address": "Address", "d_hours": "Hours", "d_services": "Services",
        "d_pricing": "Pricing", "d_access": "Accessibility", "d_notes": "Notes",
        "d_website": "Website", "d_visit": "Visit website",
        # about
        "about_title": "About Marburg Repair Hub",
        "about_lead": ("Marburg Repair Hub is a university-supported platform that helps "
                       "residents find local repair cafés, professional repair services, and "
                       "community resources to fix electronics, bikes, and household items "
                       "instead of throwing them away."),
        "about_mission_t": "Our mission",
        "about_mission_b": ("Every repaired device is one less item in a landfill and a real cut "
                            "in carbon emissions. We want repair to be the easy, obvious first "
                            "choice in Marburg."),
        "about_do_t": "What we do",
        "about_do_1": "Map every repair café and professional repair service across Marburg.",
        "about_do_2": "Let you search by what you need fixed — phones, laptops, bikes and more.",
        "about_do_3": "Show opening hours, pricing, accessibility and contact details.",
        "about_impact_t": "Our impact",
        "about_who_t": "Who we are",
        "about_who_b": ("The platform is a project of the Philipps University of Marburg, built "
                        "with and for the local community."),
        "stat_co2": "CO₂ saved by repairing a single smartphone.",
        "stat_count": "repair cafés and services listed.",
        "stat_free": "to use — most community cafés run on donations.",
        # contact
        "contact_title": "Contact Us",
        "c_name": "Name", "c_email": "Email", "c_subject": "Subject", "c_message": "Message",
        "c_send": "Send Message", "c_success": "Message sent! We'll reply soon.",
        "c_ph_name": "Your Name", "c_ph_email": "Your Email",
        "c_ph_subject": "How can we help?", "c_ph_message": "Write your message here...",
        # faq
        "faq_title": "Frequently Asked Questions",
        # footer
        "f_quick": "Quick Links", "f_legal": "Legal Links", "f_contact": "Contact",
        "f_follow": "Follow Us", "f_about": "About", "f_services": "Services",
        "f_privacy": "Privacy Policy", "f_terms": "Terms of Service",
        "f_cookie": "Cookie Policy", "f_imprint": "Imprint",
        "f_rights": "© 2026 Marburg Repair Help Platform — Philipps University of Marburg. All rights reserved.",
        # admin
        "a_login_title": "Admin Login",
        "a_password": "Password", "a_login": "Log in", "a_wrong": "Incorrect password.",
        "a_title": "Site Settings", "a_intro": "Choose a section to edit. Each section stays minimized until you select Edit.",
        "a_logout": "Log out",
        "a_email_sec": "Contact Email Configuration",
        "a_email_label": "Receiver email (Contact form)",
        "a_phone_label": "Public phone number",
        "a_save": "Save", "a_edit": "Edit", "a_close": "Close", "a_remove": "Remove", "a_add": "Add",
        "a_faq_sec": "FAQ Management",
        "a_cafe_sec": "Café Management",
        "a_q_en": "Question (EN)", "a_a_en": "Answer (EN)",
        "a_q_de": "Question (DE)", "a_a_de": "Answer (DE)",
        "a_cafe_name": "Name", "a_cafe_addr": "Address", "a_cafe_hours": "Hours",
        "a_cafe_price": "Pricing", "a_cafe_access": "Accessibility", "a_cafe_notes": "Notes",
        "a_cafe_web": "Website", "a_cafe_lat": "Latitude", "a_cafe_lng": "Longitude",
        "a_cafe_services": "Services offered (select all that apply)",
        "a_saved": "Changes saved.",
    },
    "de": {
        "site_name": "Marburg Reparatur-Hilfe",
        "nav_map": "Karte", "nav_services": "Leistungen", "nav_about": "Über uns",
        "nav_contact": "Kontakt", "nav_faqs": "FAQ",
        "nav_partner": "Partner werden",
        "partner_coming_soon": "Die Funktion 'Partner werden' befindet sich derzeit in Entwicklung und wird in einer zukünftigen Version von Marburg Repair Hub verfügbar sein.",
        "hero_title": "Reparieren statt Wegwerfen",
        "hero_sub": "Finde Reparaturdienste in Marburg und reduziere Elektroschrott.",
        "search_placeholder": "Was möchtest du reparieren?",
        "search_btn": "Suchen",
        "categories_title": "Beliebte Reparatur-Kategorien",
        "co2_title": "🌱 Umweltauswirkung",
        "map_title": "Reparaturorte in Marburg",
        "sidebar_search": "Reparatur-Cafés oder Gerätetyp suchen...",
        "all_services": "Alle Leistungen",
        "no_results": "Keine passenden Orte gefunden.",
        "clear_filter": "Alle anzeigen",
        "d_address": "Adresse", "d_hours": "Öffnungszeiten", "d_services": "Leistungen",
        "d_pricing": "Preise", "d_access": "Barrierefreiheit", "d_notes": "Hinweise",
        "d_website": "Webseite", "d_visit": "Webseite besuchen",
        "about_title": "Über Marburg Repair Hub",
        "about_lead": ("Marburg Repair Hub ist eine von der Universität unterstützte Plattform, "
                       "die Einwohnern hilft, lokale Reparatur-Cafés, professionelle "
                       "Reparaturdienste und Gemeinschaftsangebote zu finden, um Elektronik, "
                       "Fahrräder und Haushaltsgeräte zu reparieren, statt sie wegzuwerfen."),
        "about_mission_t": "Unsere Mission",
        "about_mission_b": ("Jedes reparierte Gerät ist ein Stück weniger Müll und spart CO₂. "
                            "Wir möchten, dass Reparatur in Marburg die einfache und "
                            "naheliegende erste Wahl wird."),
        "about_do_t": "Was wir tun",
        "about_do_1": "Wir kartieren alle Reparatur-Cafés und Dienste in Marburg.",
        "about_do_2": "Suche nach Reparaturbedarf — Handys, Laptops, Fahrräder und mehr.",
        "about_do_3": "Wir zeigen Öffnungszeiten, Preise, Barrierefreiheit und Kontaktdaten.",
        "about_impact_t": "Unsere Wirkung",
        "about_who_t": "Wer wir sind",
        "about_who_b": ("Die Plattform ist ein Projekt der Philipps-Universität Marburg, "
                        "entwickelt mit und für die lokale Gemeinschaft."),
        "stat_co2": "CO₂ gespart durch die Reparatur eines einzigen Smartphones.",
        "stat_count": "Reparatur-Cafés und Dienste gelistet.",
        "stat_free": "Nutzung kostenlos — viele Cafés leben von Spenden.",
        "contact_title": "Kontakt",
        "c_name": "Name", "c_email": "E-Mail", "c_subject": "Betreff", "c_message": "Nachricht",
        "c_send": "Nachricht senden", "c_success": "Nachricht gesendet! Wir melden uns bald.",
        "c_ph_name": "Dein Name", "c_ph_email": "Deine E-Mail",
        "c_ph_subject": "Wie können wir helfen?", "c_ph_message": "Schreibe hier deine Nachricht...",
        "faq_title": "Häufig gestellte Fragen",
        "f_quick": "Schnellzugriff", "f_legal": "Rechtliches", "f_contact": "Kontakt",
        "f_follow": "Folge uns", "f_about": "Über uns", "f_services": "Leistungen",
        "f_privacy": "Datenschutz", "f_terms": "Nutzungsbedingungen",
        "f_cookie": "Cookie-Richtlinie", "f_imprint": "Impressum",
        "f_rights": "© 2026 Marburg Repair Help Plattform — Philipps-Universität Marburg. Alle Rechte vorbehalten.",
        "a_login_title": "Admin-Anmeldung",
        "a_password": "Passwort", "a_login": "Anmelden", "a_wrong": "Falsches Passwort.",
        "a_title": "Seiteneinstellungen", "a_intro": "Wähle einen Bereich zum Bearbeiten. Jeder Bereich bleibt minimiert, bis du auf Bearbeiten klickst.",
        "a_logout": "Abmelden",
        "a_email_sec": "Kontakt-E-Mail-Konfiguration",
        "a_email_label": "Empfänger-E-Mail (Kontaktformular)",
        "a_phone_label": "Öffentliche Telefonnummer",
        "a_save": "Speichern", "a_edit": "Bearbeiten", "a_close": "Schließen",
        "a_remove": "Entfernen", "a_add": "Hinzufügen",
        "a_faq_sec": "FAQ-Verwaltung",
        "a_cafe_sec": "Café-Verwaltung",
        "a_q_en": "Frage (EN)", "a_a_en": "Antwort (EN)",
        "a_q_de": "Frage (DE)", "a_a_de": "Antwort (DE)",
        "a_cafe_name": "Name", "a_cafe_addr": "Adresse", "a_cafe_hours": "Öffnungszeiten",
        "a_cafe_price": "Preise", "a_cafe_access": "Barrierefreiheit", "a_cafe_notes": "Hinweise",
        "a_cafe_web": "Webseite", "a_cafe_lat": "Breitengrad", "a_cafe_lng": "Längengrad",
        "a_cafe_services": "Angebotene Leistungen (alle zutreffenden auswählen)",
        "a_saved": "Änderungen gespeichert.",
    },
}


# --------------------------------------------------------------------------- #
#  Database helpers
# --------------------------------------------------------------------------- #
def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(DATABASE)
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys = ON")
    return g.db


@app.teardown_appcontext
def close_db(exc):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db():
    """Create the schema and seed it the first time the app runs."""
    need_seed = not os.path.exists(DATABASE)
    db = sqlite3.connect(DATABASE)
    db.row_factory = sqlite3.Row
    db.execute("PRAGMA foreign_keys = ON")

    # (Re)create tables if the cafes table is missing.
    has_tables = db.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='cafes'"
    ).fetchone()
    if not has_tables:
        with open(SCHEMA, "r", encoding="utf-8") as f:
            db.executescript(f.read())
        need_seed = True

    if need_seed:
        _seed(db)
    db.commit()
    db.close()


def _seed(db):
    # Settings
    db.execute("INSERT OR REPLACE INTO settings(key, value) VALUES('contact_email', ?)",
               ("info@marburgrepair.de",))
    db.execute("INSERT OR REPLACE INTO settings(key, value) VALUES('contact_phone', ?)",
               ("+49 123 456789",))

    # Services  (slug, en, de, icon, featured)
    services = [
        ("phone",      "Phones",        "Handys",                 "📱", 1),
        ("laptop",     "Laptops",       "Laptops",                "💻", 1),
        ("audio",      "Audio & Radio", "Audio & Radio",          "📻", 1),
        ("bike",       "Bikes",         "Fahrräder",              "🚲", 1),
        ("household",  "Household",     "Haushalt",               "🏠", 1),
        ("tools",      "Tools & DIY",   "Werkzeug & Heimwerken",  "🛠", 1),
        ("clothing",   "Clothing",      "Kleidung",               "🧵", 0),
        ("instruments","Instruments",   "Instrumente",            "🎵", 0),
    ]
    db.executemany(
        "INSERT INTO services(slug, name_en, name_de, icon, featured) VALUES(?,?,?,?,?)",
        services,
    )
    svc_id = {row["slug"]: row["id"]
              for row in db.execute("SELECT id, slug FROM services")}

    # Cafes  (name, address, hours, pricing, accessibility, notes, website, lat, lng, [service slugs])
    cafes = [
        ("Repair Café Cappel", "August-Bebel-Platz, 35043 Marburg-Cappel", "Saturday 10:00 – 14:00",
         "Free (donations welcome)", "Wheelchair accessible", "Volunteer-based community repair café",
         "https://example.com", 50.7941, 8.8076, ["phone", "laptop", "audio", "household", "clothing"]),
        ("ReparierBar Marburg", "Biegenstr. 17, 35037 Marburg", "By appointment",
         "Free", "Partially accessible", "Online appointment booking",
         "https://example.com", 50.8079, 8.7696, ["household", "clothing", "phone", "laptop"]),
        ("ReparierBar Wehrshausen", "Wehrshäuser Str. 2, 35041 Marburg", "By appointment",
         "Free", "Unknown", "No large appliances",
         "https://example.com", 50.7759, 8.7246, ["household", "audio", "bike", "clothing"]),
        ("Repair Café Cölbe", "Friedhofstr. 4, 35091 Cölbe", "By phone/email",
         "Free", "Unknown", "Outside Marburg",
         "https://example.com", 50.8476, 8.7853, ["phone", "laptop", "clothing", "household", "bike"]),
        ("RADikate", "Heusingerstr. 2, 35037 Marburg", "Open hours – walk in",
         "Free", "Unknown", "Community bicycle repair",
         "https://example.com", 50.8124, 8.7718, ["bike"]),
        ("Radwerkstatt Radau", "Schwanallee 27–31, 35037 Marburg", "Open hours – walk in",
         "Membership-based", "Unknown", "Not completely free",
         "https://example.com", 50.8182, 8.7859, ["bike"]),
        ("Hobby Radwerkstatt (Soziale Hilfe Marburg e.V.)", "Zimmerplatzweg 2, 35043 Marburg-Cappel",
         "Open hours – self repair", "Very low cost", "Unknown", "DIY repair with tools provided",
         "https://example.com", 50.7954, 8.8063, ["bike", "tools"]),
        ("Siebert Audio-Video-Service GmbH", "Stephan-Niderehe-Str. 36, 35037 Marburg",
         "Open hours – walk in", "Paid", "Unknown", "Professional repair service",
         "https://example.com", 50.8231, 8.7789, ["audio", "household"]),
        ("HandyDoctor", "Barfüßerstraße 32, 35037 Marburg", "Open hours – walk in",
         "Paid", "Unknown", "Phone and electronics repair",
         "https://example.com", 50.8093, 8.7702, ["phone", "laptop"]),
        ("Inspired4u", "Am Grün 34, 35037 Marburg", "Open hours – walk in",
         "Paid", "Unknown", "IT and software services",
         "https://example.com", 50.8084, 8.7736, ["laptop"]),
        ("EBC-Marburg", "Weidenhäuser Straße 60, 35037 Marburg", "Open hours – walk in",
         "Paid", "Unknown", "Apple specialist",
         "https://example.com", 50.8127, 8.7739, ["phone", "laptop"]),
        ("Fuchselektro", "Wilhelmstraße 16, 35037 Marburg", "Open hours – walk in",
         "Paid", "Unknown", "Miele, AEG, Bosch, Siemens",
         "https://example.com", 50.8099, 8.7708, ["household"]),
        ("Musikhaus am Biegen", "Biegenstr. 20, 35037 Marburg", "Open hours / by appointment",
         "Paid", "Unknown", "Instrument repair",
         "https://example.com", 50.8076, 8.7691, ["instruments"]),
    ]
    for c in cafes:
        cur = db.execute(
            """INSERT INTO cafes(name, address, hours, pricing, accessibility, notes, website, lat, lng)
               VALUES(?,?,?,?,?,?,?,?,?)""",
            c[:9],
        )
        cid = cur.lastrowid
        for slug in c[9]:
            db.execute("INSERT INTO cafe_services(cafe_id, service_id) VALUES(?,?)",
                       (cid, svc_id[slug]))

    # FAQs (bilingual)
    faqs = [
        ("What is Marburg Repair Hub?",
         "Marburg Repair Hub is a university-supported platform that helps residents find local "
         "repair cafés, professional repair services, and community resources to fix electronics, "
         "bikes, and household items instead of throwing them away.",
         "Was ist der Marburg Repair Hub?",
         "Der Marburg Repair Hub ist eine von der Universität unterstützte Plattform, die "
         "Einwohnern hilft, lokale Reparatur-Cafés und Dienste zu finden, um Geräte zu reparieren, "
         "statt sie wegzuwerfen."),
        ("Is it free to use the platform and attend repair cafés?",
         "Using our website to search for locations is completely free. Local community repair cafés "
         "are usually free or run on voluntary donations, though you may need to pay for replacement parts.",
         "Ist die Nutzung der Plattform und der Reparatur-Cafés kostenlos?",
         "Die Nutzung unserer Webseite ist komplett kostenlos. Gemeinschaftliche Reparatur-Cafés "
         "sind meist kostenlos oder spendenbasiert; Ersatzteile können kostenpflichtig sein."),
        ("How does repairing items help the environment?",
         "Extending the lifespan of your products reduces electronic waste and cuts carbon emissions. "
         "Repairing a single smartphone saves approximately 70 kg of CO₂.",
         "Wie hilft Reparieren der Umwelt?",
         "Eine längere Lebensdauer der Produkte reduziert Elektroschrott und CO₂-Emissionen. "
         "Die Reparatur eines einzigen Smartphones spart etwa 70 kg CO₂."),
    ]
    for i, fq in enumerate(faqs):
        db.execute(
            """INSERT INTO faqs(question_en, answer_en, question_de, answer_de, position)
               VALUES(?,?,?,?,?)""",
            (fq[0], fq[1], fq[2], fq[3], i),
        )


# --------------------------------------------------------------------------- #
#  Language + context injection
# --------------------------------------------------------------------------- #
@app.before_request
def ensure_lang():
    if session.get("lang") not in SUPPORTED_LANGS:
        # naive browser-preference detection
        accept = (request.accept_languages.best_match(SUPPORTED_LANGS)
                  if request.accept_languages else None)
        session["lang"] = accept or "en"


def current_lang():
    return session.get("lang", "en")


def get_settings():
    rows = get_db().execute("SELECT key, value FROM settings").fetchall()
    return {r["key"]: r["value"] for r in rows}


@app.context_processor
def inject_globals():
    lang = current_lang()
    return {
        "lang": lang,
        "t": STRINGS[lang],
        "settings": get_settings(),
        "supported_langs": SUPPORTED_LANGS,
    }


@app.route("/lang/<code>")
def set_lang(code):
    if code in SUPPORTED_LANGS:
        session["lang"] = code
    return redirect(request.referrer or url_for("index"))


# --------------------------------------------------------------------------- #
#  Data access helpers
# --------------------------------------------------------------------------- #
def fetch_cafes():
    """Return cafes with their services attached, ready for templates / JSON."""
    db = get_db()
    rows = db.execute("SELECT * FROM cafes ORDER BY name").fetchall()
    cafes = []
    for r in rows:
        svc = db.execute(
            """SELECT s.slug, s.name_en, s.name_de
               FROM services s JOIN cafe_services cs ON cs.service_id = s.id
               WHERE cs.cafe_id = ? ORDER BY s.name_en""",
            (r["id"],),
        ).fetchall()
        cafes.append({
            "id": r["id"], "name": r["name"], "address": r["address"],
            "hours": r["hours"], "pricing": r["pricing"],
            "accessibility": r["accessibility"], "notes": r["notes"],
            "website": r["website"], "lat": r["lat"], "lng": r["lng"],
            "slugs": [s["slug"] for s in svc],
            "services_en": [s["name_en"] for s in svc],
            "services_de": [s["name_de"] for s in svc],
        })
    return cafes


def fetch_services():
    return get_db().execute("SELECT * FROM services ORDER BY featured DESC, name_en").fetchall()


def fetch_faqs():
    return get_db().execute("SELECT * FROM faqs ORDER BY position, id").fetchall()


# --------------------------------------------------------------------------- #
#  Public routes
# --------------------------------------------------------------------------- #
@app.route("/")
def index():
    cafes = fetch_cafes()
    services = fetch_services()
    featured = [s for s in services if s["featured"]]
    return render_template("index.html", cafes=cafes,
                           services=services, featured=featured)


@app.route("/about")
def about():
    return render_template("about.html", cafe_count=len(fetch_cafes()))


@app.route("/faq")
def faq():
    return render_template("faq.html", faqs=fetch_faqs())


@app.route("/contact", methods=["GET", "POST"])
def contact():
    if request.method == "POST":
        db = get_db()
        db.execute(
            "INSERT INTO messages(name, email, subject, body) VALUES(?,?,?,?)",
            (request.form.get("name"), request.form.get("email"),
             request.form.get("subject"), request.form.get("message")),
        )
        db.commit()
        # The configured receiver address is where this would be emailed.
        receiver = get_settings().get("contact_email")
        app.logger.info("New contact message queued for %s", receiver)
        flash(STRINGS[current_lang()]["c_success"], "success")
        return redirect(url_for("contact"))
    return render_template("contact.html")


@app.route("/api/cafes")
def api_cafes():
    """JSON feed (handy for debugging / future use)."""
    return jsonify(fetch_cafes())


# --------------------------------------------------------------------------- #
#  Admin: authentication
# --------------------------------------------------------------------------- #
def admin_required():
    if not session.get("admin"):
        abort(403)


@app.route("/admin", methods=["GET", "POST"])
def admin():
    # Login handling
    if request.method == "POST" and "password" in request.form:
        if request.form["password"] == ADMIN_PASSWORD:
            session["admin"] = True
            return redirect(url_for("admin"))
        flash(STRINGS[current_lang()]["a_wrong"], "error")
        return render_template("admin_login.html")

    if not session.get("admin"):
        return render_template("admin_login.html")

    return render_template(
        "admin.html",
        cafes=fetch_cafes(),
        services=fetch_services(),
        faqs=fetch_faqs(),
    )


@app.route("/admin/logout")
def admin_logout():
    session.pop("admin", None)
    return redirect(url_for("index"))


# --------------------------------------------------------------------------- #
#  Admin: actions
# --------------------------------------------------------------------------- #
@app.route("/admin/settings", methods=["POST"])
def admin_settings():
    admin_required()
    db = get_db()
    db.execute("INSERT OR REPLACE INTO settings(key, value) VALUES('contact_email', ?)",
               (request.form.get("contact_email", "").strip(),))
    db.execute("INSERT OR REPLACE INTO settings(key, value) VALUES('contact_phone', ?)",
               (request.form.get("contact_phone", "").strip(),))
    db.commit()
    flash(STRINGS[current_lang()]["a_saved"], "success")
    return redirect(url_for("admin"))


@app.route("/admin/faq/add", methods=["POST"])
def admin_faq_add():
    admin_required()
    db = get_db()
    pos = db.execute("SELECT COALESCE(MAX(position), -1) + 1 AS p FROM faqs").fetchone()["p"]
    db.execute(
        """INSERT INTO faqs(question_en, answer_en, question_de, answer_de, position)
           VALUES(?,?,?,?,?)""",
        (request.form.get("question_en", "").strip(),
         request.form.get("answer_en", "").strip(),
         request.form.get("question_de", "").strip(),
         request.form.get("answer_de", "").strip(),
         pos),
    )
    db.commit()
    flash(STRINGS[current_lang()]["a_saved"], "success")
    return redirect(url_for("admin"))


@app.route("/admin/faq/delete/<int:faq_id>", methods=["POST"])
def admin_faq_delete(faq_id):
    admin_required()
    db = get_db()
    db.execute("DELETE FROM faqs WHERE id = ?", (faq_id,))
    db.commit()
    flash(STRINGS[current_lang()]["a_saved"], "success")
    return redirect(url_for("admin"))


@app.route("/admin/cafe/add", methods=["POST"])
def admin_cafe_add():
    admin_required()
    db = get_db()

    def num(field):
        try:
            return float(request.form.get(field, ""))
        except (TypeError, ValueError):
            return None

    cur = db.execute(
        """INSERT INTO cafes(name, address, hours, pricing, accessibility, notes, website, lat, lng)
           VALUES(?,?,?,?,?,?,?,?,?)""",
        (request.form.get("name", "").strip(),
         request.form.get("address", "").strip(),
         request.form.get("hours", "").strip(),
         request.form.get("pricing", "").strip(),
         request.form.get("accessibility", "").strip(),
         request.form.get("notes", "").strip(),
         request.form.get("website", "").strip(),
         num("lat"), num("lng")),
    )
    cid = cur.lastrowid
    for sid in request.form.getlist("services"):
        db.execute("INSERT OR IGNORE INTO cafe_services(cafe_id, service_id) VALUES(?,?)",
                   (cid, int(sid)))
    db.commit()
    flash(STRINGS[current_lang()]["a_saved"], "success")
    return redirect(url_for("admin"))

@app.route("/admin/cafe/edit/<int:cafe_id>", methods=["POST"])
def admin_cafe_edit(cafe_id):
    admin_required()
    db = get_db()

    def num(field):
        try:
            return float(request.form.get(field, ""))
        except (TypeError, ValueError):
            return None

    db.execute(
        """UPDATE cafes
           SET name=?, address=?, hours=?, pricing=?, accessibility=?,
               notes=?, website=?, lat=?, lng=?
           WHERE id=?""",
        (request.form.get("name", "").strip(),
         request.form.get("address", "").strip(),
         request.form.get("hours", "").strip(),
         request.form.get("pricing", "").strip(),
         request.form.get("accessibility", "").strip(),
         request.form.get("notes", "").strip(),
         request.form.get("website", "").strip(),
         num("lat"), num("lng"), cafe_id),
    )
    db.execute("DELETE FROM cafe_services WHERE cafe_id = ?", (cafe_id,))
    for sid in request.form.getlist("services"):
        db.execute("INSERT OR IGNORE INTO cafe_services(cafe_id, service_id) VALUES(?,?)",
                   (cafe_id, int(sid)))
    db.commit()
    flash(STRINGS[current_lang()]["a_saved"], "success")
    return redirect(url_for("admin"))

@app.route("/admin/cafe/delete/<int:cafe_id>", methods=["POST"])
def admin_cafe_delete(cafe_id):
    admin_required()
    db = get_db()
    db.execute("DELETE FROM cafe_services WHERE cafe_id = ?", (cafe_id,))
    db.execute("DELETE FROM cafes WHERE id = ?", (cafe_id,))
    db.commit()
    flash(STRINGS[current_lang()]["a_saved"], "success")
    return redirect(url_for("admin"))


# --------------------------------------------------------------------------- #
#  Entrypoint
# --------------------------------------------------------------------------- #
with app.app_context():
    init_db()

if __name__ == "__main__":
    app.run(debug=True)
