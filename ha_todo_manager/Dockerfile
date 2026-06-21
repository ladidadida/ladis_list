# ARG must be declared before the first FROM to be usable in FROM instructions
ARG BUILD_FROM=ghcr.io/home-assistant/amd64-base-python:3.13-alpine3.22

# Stage 1 – Frontend: build the React/Vite app
# Always build on amd64 – output is pure JS and platform-independent
FROM --platform=linux/amd64 node:22-alpine AS frontend-builder
WORKDIR /build/frontend
RUN corepack enable && corepack prepare pnpm@latest --activate
COPY ha_todo_manager/frontend/package.json ha_todo_manager/frontend/pnpm-lock.yaml ./
RUN pnpm install --frozen-lockfile
COPY ha_todo_manager/frontend/ .
RUN pnpm run build

# Stage 2 – Backend: install into a venv as a proper wheel
# .git and the ha_todo_manager/ subdir are copied keeping their original relative
# layout (.git as a sibling of ha_todo_manager/, not flattened together) so that
# hatch-vcs's `root = ".."` (see ha_todo_manager/pyproject.toml) resolves the same
# way here as it does in a local checkout.
FROM ghcr.io/astral-sh/uv:python3.13-alpine AS backend-builder
RUN apk add --no-cache git
WORKDIR /app
COPY .git/ ./.git/
COPY ha_todo_manager/pyproject.toml ha_todo_manager/uv.lock ha_todo_manager/README.md ha_todo_manager/LICENSE ./ha_todo_manager/
COPY ha_todo_manager/src/ ./ha_todo_manager/src/
# Bundle the compiled frontend into the package so it is included in the wheel.
COPY --from=frontend-builder /build/frontend/dist ./ha_todo_manager/src/ha_todo_manager/frontend/dist/
WORKDIR /app/ha_todo_manager
RUN uv sync --no-dev --frozen --no-editable

# Stage 3 – Release: HA base image with only runtime artefacts
FROM ${BUILD_FROM}

ARG BUILD_VERSION=unknown
LABEL \
    io.hass.name="Todo Manager" \
    io.hass.description="A Kanban-style todo manager for Home Assistant." \
    io.hass.type="addon" \
    io.hass.version="${BUILD_VERSION}"

WORKDIR /app

COPY --from=backend-builder /app/ha_todo_manager/.venv /app/.venv
ENV PATH="/app/.venv/bin:$PATH"

COPY ha_todo_manager/run.sh /run.sh
RUN chmod a+x /run.sh

CMD ["/run.sh"]
