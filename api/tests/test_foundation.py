from fastapi.testclient import TestClient

from api.main import app

client = TestClient(app)
headers = {"Authorization": "Bearer demo-campus-a"}


def test_health():
    assert client.get("/health").json() == {"status": "ok"}


def test_search_filters_and_hides_private_fields():
    response = client.get("/api/v1/alumni?q=energy&graduation_year=2018", headers=headers)
    assert response.status_code == 200
    items = response.json()["items"]
    assert [item["id"] for item in items] == ["alum-001"]
    assert "contact_email" not in items[0]
    assert "tenant_id" not in items[0]


def test_cursor_advances_to_next_visible_record():
    first = client.get("/api/v1/alumni?limit=1", headers=headers).json()
    second = client.get("/api/v1/alumni", headers=headers, params={"cursor": first["next_cursor"]}).json()
    assert [row["id"] for row in second["items"]] == ["alum-002"]
    assert second["next_cursor"] is None


def test_read_requires_credentials_and_scope():
    assert client.get("/api/v1/alumni").status_code == 401
    denied = {"Authorization": "Bearer demo-proposals-only"}
    assert client.get("/api/v1/alumni", headers=denied).status_code == 403


def test_profile_lookup_is_tenant_scoped():
    assert client.get("/api/v1/alumni/alum-001", headers=headers).status_code == 200
    assert client.get("/api/v1/alumni/alum-003", headers=headers).status_code == 404


def test_checked_in_contract_matches_server():
    import json
    from pathlib import Path

    contract = Path(__file__).resolve().parents[2] / "contracts" / "openapi.json"
    assert json.loads(contract.read_text(encoding="utf-8")) == app.openapi()


def test_desktop_can_send_authorization_header():
    response = client.options("/api/v1/alumni", headers={
        "Origin": "http://localhost:3000",
        "Access-Control-Request-Method": "GET",
        "Access-Control-Request-Headers": "Authorization",
    })
    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://localhost:3000"
