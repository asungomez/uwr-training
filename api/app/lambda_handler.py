"""AWS Lambda entrypoint.

Wraps the FastAPI ASGI app with Mangum so API Gateway (HTTP API v2) events are
translated to ASGI and back. The rest of the app is unchanged — locally and in the
dev/test stacks it still runs under uvicorn (`app.main:app`); only this thin adapter
is Lambda-specific.
"""

from mangum import Mangum

from app.main import app

# `handler` is the function AWS invokes (module path `app.lambda_handler.handler`).
# lifespan="off": FastAPI has no startup/shutdown hooks here, and Lambda's freeze/thaw
# model doesn't map cleanly onto ASGI lifespan events, so skip them.
handler = Mangum(app, lifespan="off")
