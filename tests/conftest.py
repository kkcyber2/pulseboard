import pytest
from fastapi.testclient import TestClient

from pulseboard import app as app_module


@pytest.fixture()
def client():
    app_module.store.clear()
    app_module.seed_demo(app_module.store, points=30)
    with TestClient(app_module.app) as c:
        yield c
