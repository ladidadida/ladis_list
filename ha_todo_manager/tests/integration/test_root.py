"""Integration test for the root route (SPA / placeholder serving)."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient


@pytest.mark.integration
def test_root_serves_html(client: TestClient) -> None:
    """GET / must always return something (placeholder or built SPA), never 404."""
    response = client.get("/")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
