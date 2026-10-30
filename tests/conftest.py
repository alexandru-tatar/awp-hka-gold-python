"""Testumgebung: Betriebsmodus mit festem Testschlüssel statt echtem Portal."""

import os
import time

os.environ.pop("PORTAL_DEV", None)
os.environ["PORTAL_ENV"] = "test"
os.environ["PORTAL_ISSUER"] = "https://portal.test/"

import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import rsa
from fastapi.testclient import TestClient

from app.main import app, portal
from platform_sdk.jwks import JwksCache

PRIVATE_KEY = rsa.generate_private_key(public_exponent=65537, key_size=2048)
portal.jwks = JwksCache.static({"test-key": PRIVATE_KEY.public_key()})


def make_token(**overrides) -> str:
    now = int(time.time())
    claims = {
        "iss": "https://portal.test/",
        "aud": [portal.config.slug, "portal", "adapters"],
        "sub": "test-person",
        "name": "Erika Musterfrau",
        "roles": ["student"],
        "v": 1,
        "iat": now,
        "exp": now + 60,
    }
    claims.update(overrides)
    return jwt.encode(claims, PRIVATE_KEY, algorithm="RS256", headers={"kid": "test-key"})


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


@pytest.fixture
def as_student():
    return {"X-Portal-Assertion": make_token(), "Accept": "text/html"}
