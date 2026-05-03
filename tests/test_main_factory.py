from __future__ import annotations

from fastapi.testclient import TestClient


def test_create_full_app_exposes_health(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("OPENCS_DATA_DIR", str(tmp_path))
    monkeypatch.delenv("LANGFUSE_PUBLIC_KEY", raising=False)
    monkeypatch.delenv("LANGFUSE_SECRET_KEY", raising=False)
    from opencs.main import create_full_app
    app = create_full_app()
    client = TestClient(app)
    resp = client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"


def test_create_full_app_admin_proposals_endpoint(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("OPENCS_DATA_DIR", str(tmp_path))
    from opencs.main import create_full_app
    client = TestClient(create_full_app())
    resp = client.get("/admin/proposals")
    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] == 0
    assert body["items"] == []
