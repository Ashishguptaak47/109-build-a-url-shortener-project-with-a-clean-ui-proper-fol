import pytest
from starlette.testclient import TestClient
from app.database import init_db, get_db
from main import app

@pytest.fixture(autouse=True)
def setup_database(tmp_path, monkeypatch):
    test_db = tmp_path / "test_urls.db"
    monkeypatch.setattr("app.config.DATABASE_PATH", str(test_db))
    monkeypatch.setattr("app.database.DATABASE_PATH", str(test_db))
    init_db()

@pytest.fixture
def client():
    return TestClient(app)

def test_home_page_loads(client):
    response = client.get("/")
    assert response.status_code == 200
    assert "Shorten, Share &amp; Track URLs" in response.text

def test_api_shorten_and_redirect(client):
    payload = {
        "url": "https://fastapi.tiangolo.com/",
        "custom_code": "fastapi-docs"
    }
    response = client.post("/api/shorten", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["code"] == "fastapi-docs"
    assert data["target_url"] == "https://fastapi.tiangolo.com/"

    # Test redirection
    redirect_res = client.get("/fastapi-docs", follow_redirects=False)
    assert redirect_res.status_code == 307
    assert redirect_res.headers["location"] == "https://fastapi.tiangolo.com/"

    # Check stats API
    stats_res = client.get("/api/links/fastapi-docs")
    assert stats_res.status_code == 200
    stats_data = stats_res.json()
    assert stats_data["link"]["clicks"] == 1
    assert len(stats_data["recent_clicks"]) == 1

def test_duplicate_custom_code(client):
    payload = {"url": "https://example.com/one", "custom_code": "mycode"}
    res1 = client.post("/api/shorten", json=payload)
    assert res1.status_code == 201

    payload2 = {"url": "https://example.com/two", "custom_code": "mycode"}
    res2 = client.post("/api/shorten", json=payload2)
    assert res2.status_code == 409

def test_html_form_shorten(client):
    res = client.post(
        "/shorten",
        data={"target_url": "https://python.org", "custom_code": "py-link", "expires_in_hours": "24"}
    )
    assert res.status_code == 200
    assert "Link Ready!" in res.text
    assert "py-link" in res.text

def test_not_found(client):
    res = client.get("/non-existent-code-xyz")
    assert res.status_code == 404
    assert "Link Inactive or Not Found" in res.text

def test_stats_view_page(client):
    client.post("/api/shorten", json={"url": "https://example.com", "custom_code": "statstest"})
    res = client.get("/stats/statstest")
    assert res.status_code == 200
    assert "Analytics for /statstest" in res.text
