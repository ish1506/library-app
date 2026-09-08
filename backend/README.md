# Library Backend

## Requirements

- Python 3.12 or later
- [uv](https://docs.astral.sh/uv/)

## Run locally

```bash
uv sync
uv run fastapi dev main.py
```

The API is available at `http://127.0.0.1:8000`, with interactive documentation at `/docs` and a health check at `/health`.
