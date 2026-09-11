from types import SimpleNamespace
from unittest.mock import AsyncMock

from fastapi.middleware.cors import CORSMiddleware
from fastapi.testclient import TestClient

import main
from main import app


def test_shutdown_disposes_async_engine(monkeypatch) -> None:
    dispose = AsyncMock()
    monkeypatch.setattr(main, "async_engine", SimpleNamespace(dispose=dispose))

    with TestClient(app) as client:
        assert client.get("/health").json() == {"status": "ok"}

    dispose.assert_awaited_once_with()


def test_cors_middleware_uses_configured_origins() -> None:
    cors_middleware = next(
        middleware
        for middleware in app.user_middleware
        if middleware.cls is CORSMiddleware
    )

    assert cors_middleware.kwargs["allow_origins"] == main.settings.allowed_cors_origins
    assert cors_middleware.kwargs["allow_credentials"] is False
