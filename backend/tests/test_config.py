from app.config import Settings


def test_allowed_cors_origins_ignores_blank_entries() -> None:
    settings = Settings(
        DATABASE_URL="postgresql+psycopg://user:password@localhost/library",
        JWT_SECRET_KEY="test-secret",
        CORS_ALLOWED_ORIGINS=" https://library-app.vercel.app, ,https://preview.vercel.app ",
    )

    assert settings.allowed_cors_origins == [
        "https://library-app.vercel.app",
        "https://preview.vercel.app",
    ]
