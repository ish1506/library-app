from types import SimpleNamespace
from unittest.mock import AsyncMock

import main
from fastapi.testclient import TestClient
from main import app


def test_shutdown_disposes_async_engine(monkeypatch) -> None:
    dispose = AsyncMock()
    monkeypatch.setattr(main, "async_engine", SimpleNamespace(dispose=dispose))

    with TestClient(app) as client:
        assert client.get("/health").json() == {"status": "ok"}

    dispose.assert_awaited_once_with()
