# uwr-training-api

FastAPI back-end. Managed with [uv](https://docs.astral.sh/uv/).

```bash
uv sync                              # install deps (incl. dev group)
uv run uvicorn app.main:app --reload # run locally
uv run ruff check .                  # lint
uv run ruff format .                 # format
uv run mypy .                        # type-check (strict)
```

Or run it in Docker from the repo root: `make run service=api`.
