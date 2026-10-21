# Automated tests – Marburg Repair Hub

Put this `tests` folder into the project folder (`marburg/tests`).

```bash
pip install pytest coverage playwright
python -m playwright install chromium     # once
python -m pytest tests -v                 # run all tests
python -m coverage run --include="*/repair_hub_test_site/app.py" -m pytest tests/test_backend.py
python -m coverage report -m              # backend coverage
```

* `test_backend.py` – unit/integration tests with the Flask test client (T01–T23)
* `test_gui.py` – browser tests with Playwright/Chromium (G01–G12); G00 saves screenshots to `tests/screenshots`
* Every test uses a fresh copy of the project and a new database in the temp folder; the real `repair_hub.db` is never changed.
* Map tiles are replaced by a blank image during GUI tests. Leaflet is loaded from the internet, or from
  `tests/node_modules` if you run `npm install leaflet@1.9.4` inside the tests folder.

Expected result (2 Oct 2026): 31 passed, 4 failed (T21, T22, T23, G05 – real defects, see technical report 4.2).
