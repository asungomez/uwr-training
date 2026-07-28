# Production image for running the FastAPI app on AWS Lambda (container image).
# Built and pushed to ECR by the deploy workflow; the Lambda function runs from it.
#
# Uses the AWS-provided Lambda Python base image, which bundles the Runtime Interface
# Client/Emulator so `CMD ["<module>.<handler>"]` is all that's needed. Deps are
# installed with uv into the image's site (no venv — Lambda runs the module directly).
FROM public.ecr.aws/lambda/python:3.12

# uv: fast, reproducible installs from the lockfile.
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy

# Install dependencies first (cached until the lockfile changes). Target the Lambda
# task root so the packages land on the runtime's import path; --no-install-project
# installs only the third-party deps, not our app (copied below).
COPY api/pyproject.toml api/uv.lock ./
RUN uv export --frozen --no-dev --no-emit-project -o requirements.txt \
    && uv pip install --system --target "${LAMBDA_TASK_ROOT}" -r requirements.txt \
    && rm requirements.txt

# App source. alembic/ isn't needed at request time (migrations run via the separate
# migrate workflow), so copy just the application package.
COPY api/app ${LAMBDA_TASK_ROOT}/app

# The handler AWS invokes: module `app.lambda_handler`, attribute `handler`.
CMD ["app.lambda_handler.handler"]
