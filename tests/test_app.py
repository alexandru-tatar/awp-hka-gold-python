from conftest import make_token


def test_healthz_ohne_anmeldung(client):
    assert client.get("/healthz").status_code == 200


def test_ohne_anmeldung_401(client):
    response = client.get("/", headers={"Accept": "text/html"})
    assert response.status_code == 401
    assert "Anmeldung fehlt" in response.text
    assert "set-cookie" not in response.headers


def test_ungueltige_anmeldung_401(client):
    response = client.get("/", headers={"X-Portal-Assertion": make_token(aud=["andere-app"])})
    assert response.status_code == 401
    assert response.headers["content-type"] == "application/problem+json"


def test_keine_api_doku(client, as_student):
    for path in ("/docs", "/redoc", "/openapi.json"):
        assert client.get(path, headers=as_student).status_code == 404


def test_startseite(client, as_student):
    response = client.get("/", headers=as_student)
    assert response.status_code == 200
    html = response.text
    assert '<html lang="de">' in html
    assert 'href="#main"' in html
    assert html.count("<h1") == 1
    assert "set-cookie" not in response.headers


def test_startseite_englisch(client, as_student):
    response = client.get("/", headers={**as_student, "Accept-Language": "en-GB,en;q=0.9"})
    assert response.status_code == 200
    html = response.text
    assert '<html lang="en">' in html
    assert "<h1>My app</h1>" in html


def test_texte_in_beiden_sprachen():
    from app.views import TEXTS

    assert set(TEXTS) == {"de", "en"}
    assert set(TEXTS["de"]) == set(TEXTS["en"])
