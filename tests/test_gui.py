"""GUI / system tests: run the real Flask server and drive it with a Chromium browser (Playwright).

External resources (Leaflet from unpkg, map tiles from Esri) are served locally so the
tests do not depend on the internet.
"""
import base64
import socket
import subprocess
import sys
import time
from pathlib import Path

import pytest
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent          # project folder (marburg)
# optional local copy of Leaflet (npm install leaflet@1.9.4 in the tests folder); otherwise loaded from the internet
LEAFLET = Path(__file__).resolve().parent / "node_modules" / "leaflet" / "dist"
BLANK_PNG = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8/x8AAwMCAO+ip1sAAAAASUVORK5CYII=")
SHOTS = Path(__file__).resolve().parent / "screenshots"


def free_port():
    s = socket.socket(); s.bind(("127.0.0.1", 0)); p = s.getsockname()[1]; s.close(); return p


@pytest.fixture(scope="module")
def server(tmp_path_factory):
    import shutil
    target = tmp_path_factory.mktemp("gui") / "site"
    shutil.copytree(ROOT, target, ignore=shutil.ignore_patterns("repair_hub.db", "__pycache__", "tests", ".idea"))
    port = free_port()
    proc = subprocess.Popen([sys.executable, "-c",
                             f"import sys; sys.path.insert(0, r'{target}'); import app; "
                             f"app.app.run(port={port}, debug=False)"],
                            cwd=target, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    for _ in range(50):
        try:
            socket.create_connection(("127.0.0.1", port), timeout=0.2).close(); break
        except OSError:
            time.sleep(0.2)
    yield f"http://127.0.0.1:{port}"
    proc.terminate()


def route_external(route):
    url = route.request.url
    if not LEAFLET.exists() and "unpkg.com" in url:
        return route.continue_()
    if "unpkg.com" in url and "/images/" in url:
        return route.fulfill(body=(LEAFLET / "images" / url.rsplit("/", 1)[1]).read_bytes(),
                             content_type="image/png")
    if "unpkg.com/leaflet" in url:
        name = "leaflet.css" if url.endswith(".css") else "leaflet.js"
        ctype = "text/css" if name.endswith("css") else "application/javascript"
        return route.fulfill(body=(LEAFLET / name).read_bytes(), content_type=ctype)
    if "arcgisonline" in url:
        return route.fulfill(body=BLANK_PNG, content_type="image/png")
    return route.continue_()


@pytest.fixture(scope="module")
def browser():
    with sync_playwright() as p:
        b = p.chromium.launch()
        yield b
        b.close()


@pytest.fixture
def page(browser):
    ctx = browser.new_context(viewport={"width": 1280, "height": 900}, locale="en-US")
    pg = ctx.new_page()
    pg.route("**/*", route_external)
    yield pg
    ctx.close()


def visible_cafes(page):
    return page.locator("#cafeList .cafe-item").count()


def test_G00_screenshots(page, server):
    """G00 (helper): capture screenshots for the user documentation."""
    SHOTS.mkdir(exist_ok=True)
    page.goto(server + "/")
    page.wait_for_selector(".leaflet-marker-icon")
    page.wait_for_timeout(800)
    page.screenshot(path=str(SHOTS / "home.png"))
    page.locator("#mapSection").screenshot(path=str(SHOTS / "map_all.png"))
    page.locator("#mapSection").scroll_into_view_if_needed()
    page.fill("#locationSearch", "bike")
    page.locator("#cafeList .cafe-item").first.click()
    page.wait_for_timeout(400)
    page.locator("#mapSection").screenshot(path=str(SHOTS / "map_search.png"))
    page.goto(server + "/admin")
    page.screenshot(path=str(SHOTS / "admin_login.png"))
    page.fill("input[name=password]", "12344"); page.click("button[type=submit]")
    page.click("#section-cafes .btn-edit")
    page.wait_for_timeout(300)
    page.screenshot(path=str(SHOTS / "admin_panel.png"), full_page=False)


def test_G01_map_shows_all_markers(page, server):
    """G01: the map loads and shows one marker per café (13)."""
    page.goto(server + "/")
    page.wait_for_selector(".leaflet-marker-icon")
    assert page.locator(".leaflet-marker-icon").count() == 13
    assert visible_cafes(page) == 13


def test_G02_live_search_by_service(page, server):
    """G02: typing 'bike' in the sidebar search shows only locations offering bike repair."""
    page.goto(server + "/")
    page.fill("#locationSearch", "bike")
    assert visible_cafes(page) == 5
    assert page.locator(".leaflet-marker-icon").count() == 5


def test_G03_live_search_by_name(page, server):
    """G03: searching by name finds the matching location."""
    page.goto(server + "/")
    page.fill("#locationSearch", "handydoctor")
    assert visible_cafes(page) == 1


def test_G04_no_results_message(page, server):
    """G04: a search without matches shows the 'no results' message."""
    page.goto(server + "/")
    page.fill("#locationSearch", "xyz123")
    assert visible_cafes(page) == 0
    assert page.locator("#noResults").is_visible()


def test_G05_search_spelling_variants(page, server):
    """G05: searching 'lap top' should find the same locations as 'laptop'."""
    page.goto(server + "/")
    page.fill("#locationSearch", "laptop")
    expected = visible_cafes(page)
    page.fill("#locationSearch", "lap top")
    assert visible_cafes(page) == expected, f"'lap top' found {visible_cafes(page)} instead of {expected}"


def test_G06_category_filter(page, server):
    """G06: clicking the 'Bikes' category card filters the list; clicking again resets it."""
    page.goto(server + "/")
    # the cards sit in a continuously animated slider, so the click is dispatched directly
    card = page.locator(".category-card[data-service='bike']").first
    card.dispatch_event("click")
    assert visible_cafes(page) == 5
    card.dispatch_event("click")
    assert visible_cafes(page) == 13


def test_G07_details_panel(page, server):
    """G07: clicking a location in the list shows its details."""
    page.goto(server + "/")
    page.locator("#cafeList .cafe-item", has_text="Repair Café Cappel").click()
    details = page.locator("#locationDetails")
    assert "August-Bebel-Platz" in details.inner_text()
    assert "Saturday 10:00" in details.inner_text()


def test_G08_hero_search(page, server):
    """G08: the search box in the hero section feeds the sidebar search."""
    page.goto(server + "/")
    page.fill(".search-box input", "phone")
    page.click(".search-box button")
    assert page.input_value("#locationSearch") == "phone"
    assert visible_cafes(page) == 5


def test_G09_language_toggle(page, server):
    """G09: the DE/EN switch changes the interface language."""
    page.goto(server + "/")
    page.click(".lang-switch >> text=DE")
    assert "Reparieren statt Wegwerfen" in page.inner_text("h1")
    page.click(".lang-switch >> text=EN")
    assert "Repair Instead of Replace" in page.inner_text("h1")


def test_G10_contact_form(page, server):
    """G10: submitting the contact form shows a confirmation message."""
    page.goto(server + "/contact")
    page.fill("#name", "Test User"); page.fill("#email", "test@example.org")
    page.fill("#subject", "Question"); page.fill("#message", "Hello!")
    page.click("button[type=submit]")
    assert page.locator(".flash-success").is_visible()


def test_G11_admin_add_cafe_via_ui(page, server):
    """G11: an admin logs in, adds a café in the form and it appears on the home page."""
    page.goto(server + "/admin")
    page.fill("input[name=password]", "12344")
    page.click("button[type=submit]")
    page.click("#section-cafes .btn-edit")
    form = page.locator("form[action$='/admin/cafe/add']")
    form.locator("input[name=name]").fill("GUI Test Café")
    form.locator("input[name=lat]").fill("50.80")
    form.locator("input[name=lng]").fill("8.77")
    form.locator("button[type=submit]").click()
    page.goto(server + "/")
    assert page.locator("#cafeList .cafe-item", has_text="GUI Test Café").count() == 1


def test_G12_mobile_layout(browser, server):
    """G12: on a 375 px wide phone screen the home page has no horizontal scrolling."""
    ctx = browser.new_context(viewport={"width": 375, "height": 812}, is_mobile=True)
    pg = ctx.new_page(); pg.route("**/*", route_external)
    pg.goto(server + "/")
    overflow = pg.evaluate("document.documentElement.scrollWidth - window.innerWidth")
    pg.screenshot(path=str(SHOTS / "mobile.png"))
    ctx.close()
    assert overflow <= 0, f"page is {overflow}px wider than the screen"
