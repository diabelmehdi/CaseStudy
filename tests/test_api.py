import os
os.environ.setdefault("DATABASE_URL", "sqlite:///test.db")

import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock
from app.main import app
from app.db.session import get_db


def override_get_db():
    db = MagicMock()
    db.add = MagicMock()
    db.commit = MagicMock()
    db.refresh = MagicMock(side_effect=lambda obj: setattr(obj, "id", 1) or setattr(obj, "created_at", "2026-03-21T00:00:00Z"))
    try:
        yield db
    finally:
        pass


app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)


class TestHealthEndpoint:
    def test_health_returns_ok(self):
        response = client.get("/api/v1/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"


class TestPrimesEndpoint:
    def test_valid_range(self):
        response = client.post("/api/v1/primes", json={"start": 1, "end": 10})
        assert response.status_code == 200
        data = response.json()
        assert data["primes"] == [2, 3, 5, 7]
        assert data["prime_count"] == 4

    def test_start_greater_than_end(self):
        response = client.post("/api/v1/primes", json={"start": 10, "end": 1})
        assert response.status_code == 400

    def test_range_too_large(self):
        response = client.post("/api/v1/primes", json={"start": 1, "end": 20000000})
        assert response.status_code == 400

    def test_negative_start(self):
        response = client.post("/api/v1/primes", json={"start": -1, "end": 10})
        assert response.status_code == 422

    def test_missing_fields(self):
        response = client.post("/api/v1/primes", json={})
        assert response.status_code == 422
