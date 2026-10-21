"""Backend tests (unit / integration) for the Marburg Repair Hub Flask application."""


# ---------- Database & seeding -------------------------------------------------
def test_T01_seed_data(db):
    """T01: first start creates the schema and seeds 13 cafés, 8 services, 3 FAQs."""
    assert db.execute("SELECT COUNT(*) FROM cafes").fetchone()[0] == 13
    assert db.execute("SELECT COUNT(*) FROM services").fetchone()[0] == 8
    assert db.execute("SELECT COUNT(*) FROM faqs").fetchone()[0] == 3
    assert db.execute("SELECT COUNT(*) FROM cafe_services").fetchone()[0] == 31


# ---------- Public pages ------------------------------------------------------
def test_T02_public_pages_load(client):
    """T02: all public pages answer with HTTP 200."""
    for url in ("/", "/about", "/faq", "/contact"):
        assert client.get(url).status_code == 200, url


def test_T03_home_lists_all_cafes(client, db):
    """T03: the home page lists every café by default (no filter applied)."""
    html = client.get("/").get_data(as_text=True)
    for (name,) in db.execute("SELECT name FROM cafes"):
        assert name.replace("&", "&amp;") in html or name in html


def test_T04_api_returns_cafes_with_services(client):
    """T04: /api/cafes returns all cafés including their services (many-to-many)."""
    data = client.get("/api/cafes").get_json()
    assert len(data) == 13
    cappel = next(c for c in data if c["name"] == "Repair Café Cappel")
    assert set(cappel["slugs"]) == {"phone", "laptop", "audio", "household", "clothing"}


def test_T05_language_switch(client):
    """T05: switching to German shows German UI texts; English is the default."""
    assert "Repair Instead of Replace" in client.get("/").get_data(as_text=True)
    client.get("/lang/de")
    assert "Reparieren statt Wegwerfen" in client.get("/").get_data(as_text=True)


def test_T06_unsupported_language_ignored(client):
    """T06: an unsupported language code does not change the language."""
    client.get("/lang/fr")
    assert "Repair Instead of Replace" in client.get("/").get_data(as_text=True)


def test_T07_contact_form_stores_message(client, db):
    """T07: the contact form stores the message in the database and shows a confirmation."""
    r = client.post("/contact", data={"name": "Test", "email": "t@example.org",
                                      "subject": "Hi", "message": "Hello"},
                    follow_redirects=True)
    assert "Message sent" in r.get_data(as_text=True)
    assert db.execute("SELECT COUNT(*) FROM messages").fetchone()[0] == 1


def test_T08_unknown_route_404(client):
    """T08: unknown URLs return 404."""
    assert client.get("/does-not-exist").status_code == 404


def test_T09_admin_not_linked_in_navigation(client):
    """T09: the admin page is not linked in the public navigation."""
    assert 'href="/admin"' not in client.get("/").get_data(as_text=True)


# ---------- Admin authentication ---------------------------------------------
def test_T10_admin_requires_login(client):
    """T10: /admin shows the login form when not logged in."""
    html = client.get("/admin").get_data(as_text=True)
    assert 'name="password"' in html


def test_T11_wrong_password_rejected(client):
    """T11: a wrong password is rejected with an error message."""
    html = client.post("/admin", data={"password": "wrong"}).get_data(as_text=True)
    assert "Incorrect password" in html


def test_T12_correct_password_opens_panel(admin_client):
    """T12: the correct password opens the admin panel."""
    html = admin_client.get("/admin").get_data(as_text=True)
    assert "Café Management" in html


def test_T13_admin_actions_forbidden_without_login(client):
    """T13: all admin actions return 403 without login."""
    for url in ("/admin/settings", "/admin/faq/add", "/admin/faq/delete/1",
                "/admin/cafe/add", "/admin/cafe/edit/1", "/admin/cafe/delete/1"):
        assert client.post(url).status_code == 403, url


def test_T14_logout(admin_client):
    """T14: logging out removes admin access."""
    admin_client.get("/admin/logout")
    assert admin_client.post("/admin/cafe/delete/1").status_code == 403


# ---------- Admin content management -----------------------------------------
def test_T15_add_cafe_with_services(admin_client, db):
    """T15: a new café with two services appears in the API and on the home page."""
    ids = [str(r["id"]) for r in db.execute("SELECT id FROM services WHERE slug IN ('bike','tools')")]
    admin_client.post("/admin/cafe/add", data={"name": "Test Werkstatt", "address": "Teststr. 1",
                                               "lat": "50.80", "lng": "8.77", "services": ids})
    cafe = next(c for c in admin_client.get("/api/cafes").get_json() if c["name"] == "Test Werkstatt")
    assert set(cafe["slugs"]) == {"bike", "tools"}
    assert "Test Werkstatt" in admin_client.get("/").get_data(as_text=True)


def test_T16_edit_cafe(admin_client, db):
    """T16: editing a café updates its fields and replaces its services."""
    cid = db.execute("SELECT id FROM cafes WHERE name='RADikate'").fetchone()[0]
    sid = db.execute("SELECT id FROM services WHERE slug='tools'").fetchone()[0]
    admin_client.post(f"/admin/cafe/edit/{cid}", data={"name": "RADikate Neu", "hours": "Mo 10-12",
                                                        "lat": "50.81", "lng": "8.77", "services": [str(sid)]})
    cafe = next(c for c in admin_client.get("/api/cafes").get_json() if c["id"] == cid)
    assert cafe["name"] == "RADikate Neu" and cafe["hours"] == "Mo 10-12"
    assert cafe["slugs"] == ["tools"]


def test_T17_delete_cafe(admin_client, db):
    """T17: deleting a café also removes its service links."""
    cid = db.execute("SELECT id FROM cafes WHERE name='RADikate'").fetchone()[0]
    admin_client.post(f"/admin/cafe/delete/{cid}")
    assert db.execute("SELECT COUNT(*) FROM cafes WHERE id=?", (cid,)).fetchone()[0] == 0
    assert db.execute("SELECT COUNT(*) FROM cafe_services WHERE cafe_id=?", (cid,)).fetchone()[0] == 0


def test_T18_add_and_delete_faq(admin_client, db):
    """T18: FAQs can be added (bilingual) and removed; they appear on the FAQ page."""
    admin_client.post("/admin/faq/add", data={"question_en": "Test question?", "answer_en": "Yes.",
                                              "question_de": "Testfrage?", "answer_de": "Ja."})
    assert "Test question?" in admin_client.get("/faq").get_data(as_text=True)
    admin_client.get("/lang/de")
    assert "Testfrage?" in admin_client.get("/faq").get_data(as_text=True)
    fid = db.execute("SELECT id FROM faqs WHERE question_en='Test question?'").fetchone()[0]
    admin_client.post(f"/admin/faq/delete/{fid}")
    assert "Testfrage?" not in admin_client.get("/faq").get_data(as_text=True)


def test_T19_update_contact_settings(admin_client):
    """T19: changing the contact email/phone in the admin panel updates the footer."""
    admin_client.post("/admin/settings", data={"contact_email": "repair@uni-marburg.de",
                                               "contact_phone": "+49 6421 0000"})
    html = admin_client.get("/").get_data(as_text=True)
    assert "repair@uni-marburg.de" in html and "+49 6421 0000" in html


def test_T20_invalid_coordinates_handled(admin_client):
    """T20: non-numeric coordinates do not crash the app; they are stored as empty."""
    r = admin_client.post("/admin/cafe/add", data={"name": "No Coords", "lat": "abc", "lng": ""})
    assert r.status_code == 302
    cafe = next(c for c in admin_client.get("/api/cafes").get_json() if c["name"] == "No Coords")
    assert cafe["lat"] is None and cafe["lng"] is None


def test_T21_empty_cafe_name_rejected(admin_client, db):
    """T21: a café without a name should be rejected (input validation)."""
    before = db.execute("SELECT COUNT(*) FROM cafes").fetchone()[0]
    admin_client.post("/admin/cafe/add", data={"name": "   "})
    after = db.execute("SELECT COUNT(*) FROM cafes").fetchone()[0]
    assert after == before, "café with empty name was saved"


def test_T22_contact_form_validates_input(client, db):
    """T22: the server should reject contact messages with missing fields."""
    client.post("/contact", data={"name": "", "email": "", "subject": "", "message": ""})
    assert db.execute("SELECT COUNT(*) FROM messages").fetchone()[0] == 0, \
        "empty contact message was stored"


# ---------- Static assets ------------------------------------------------------
def test_T23_css_images_exist_case_sensitive(mod):
    """T23: every image referenced in style.css exists with exactly the same file name
    (matters on Linux servers, which are case-sensitive)."""
    import re
    from pathlib import Path
    static = Path(mod.__file__).parent / "static"
    css = (static / "style.css").read_text(encoding="utf-8")
    existing = {p.name for p in (static / "images").iterdir()}
    missing = sorted({n for n in re.findall(r"images/([^'\")]+)", css) if n not in existing})
    assert not missing, f"not found (case-sensitive): {missing}"
