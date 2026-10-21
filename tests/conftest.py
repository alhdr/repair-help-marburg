"""Shared fixtures: every test gets a fresh copy of the site with a newly seeded database."""
import importlib.util
import shutil
import sqlite3
import sys
from pathlib import Path

import pytest

import tempfile

# the tests folder lives inside the project folder (marburg/tests)
SITE = Path(__file__).resolve().parent.parent
RUN_DIR = Path(tempfile.gettempdir()) / "repair_hub_test_site"


def load_app(target: Path):
    """Copy the site to `target` and import its app.py as a fresh module."""
    if target.exists():
        shutil.rmtree(target)
    shutil.copytree(SITE, target, ignore=shutil.ignore_patterns("repair_hub.db", "__pycache__", "tests", ".idea"))
    load_app.counter = getattr(load_app, "counter", 0) + 1
    name = f"repair_app_{load_app.counter}"
    spec = importlib.util.spec_from_file_location(name, target / "app.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)          # runs init_db() -> creates + seeds DB
    module.app.config["TESTING"] = True
    return module


@pytest.fixture
def mod():
    # fixed location so that code coverage can be measured across tests
    return load_app(RUN_DIR)


@pytest.fixture
def client(mod):
    return mod.app.test_client()


@pytest.fixture
def admin_client(client):
    client.post("/admin", data={"password": "12344"})
    return client


@pytest.fixture
def db(mod):
    con = sqlite3.connect(mod.DATABASE)
    con.row_factory = sqlite3.Row
    yield con
    con.close()
