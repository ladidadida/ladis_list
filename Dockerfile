# ARG must be declared before the first FROM to be usable in FROM instructions
ARG BUILD_FROM=ghcr.io/home-assistant/amd64-base-python:3.13-alpine3.22

# Stage 1 – Frontend: build the React/Vite app
FROM node:22-alpine AS frontend-builder
WORKDIR /build/frontend
RUN corepack enable && corepack prepare pnpm@latest --activate
COPY frontend/package.json frontend/pnpm-lock.yaml ./
RUN pnpm install --frozen-lockfile
COPY frontend/ .
RUN pnpm run build

# Stage 2 – Backend: install into a venv as a proper wheel
# .git is copied so hatch-vcs can resolve the version from git tags.
FROM ghcr.io/astral-sh/uv:python3.13-alpine AS backend-builder
RUN apk add --no-cache git
WORKDIR /app
COPY pyproject.toml uv.lock README.md ./
COPY src/ ./src/
COPY .git/ ./.git/
# Bundle the compiled frontend into the package so it is included in the wheel.
COPY --from=frontend-builder /build/frontend/dist ./src/ha_shopping_list/frontend/dist/
RUN uv sync --no-dev --frozen --no-editable

# Stage 3 – Release: HA base image with only runtime artefacts
FROM ${BUILD_FROM}

ARG BUILD_VERSION=unknown
LABEL \
    io.hass.name="Shopping List" \
    io.hass.description="A fast, mobile-friendly shopping list for Home Assistant." \
    io.hass.type="addon" \
    io.hass.version="${BUILD_VERSION}"

WORKDIR /app

COPY --from=backend-builder /app/.venv /app/.venv
ENV PATH="/app/.venv/bin:$PATH"

COPY run.sh /run.sh
RUN chmod a+x /run.sh

CMD ["/run.sh"]
