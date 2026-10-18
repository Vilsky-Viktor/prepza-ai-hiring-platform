# syntax=docker/dockerfile:1
FROM node:24-alpine@sha256:ebfe2f90462722a7a4de65e91990e97fe0d401c70e0e762c5b53302f905ec1c1 AS build

RUN corepack enable

WORKDIR /frontend

COPY package.json pnpm-lock.yaml pnpm-workspace.yaml ./
RUN pnpm install --frozen-lockfile

COPY . .

ARG NEXT_PUBLIC_FIREBASE_API_KEY
ARG NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN
ARG NEXT_PUBLIC_FIREBASE_PROJECT_ID
ARG NEXT_PUBLIC_FIREBASE_AUTH_EMULATOR_URL
ARG NEXT_PUBLIC_TURNSTILE_SITE_KEY
ARG FRONTEND_SENTRY_DSN
ARG NEXT_PUBLIC_ENVIRONMENT
# Optional: uploads source maps to Sentry, so stack traces show the original code. The token is a
# build secret, mounted for this step only, so it stays out of the image and the build cache.
ARG SENTRY_ORG
ARG SENTRY_PROJECT
# The commit, as the release Sentry's build plugin names (and tags errors with).
ARG SENTRY_RELEASE
RUN --mount=type=secret,id=sentry_auth_token,env=SENTRY_AUTH_TOKEN pnpm build

# Development: docker-compose.yml mounts the source, and Next reloads on change.
FROM node:24-alpine@sha256:ebfe2f90462722a7a4de65e91990e97fe0d401c70e0e762c5b53302f905ec1c1 AS dev

RUN corepack enable

WORKDIR /frontend

COPY package.json pnpm-lock.yaml pnpm-workspace.yaml ./
RUN pnpm install --frozen-lockfile

ENV NODE_ENV=development HOSTNAME=0.0.0.0 PORT=3000 WATCHPACK_POLLING=true

EXPOSE 3000

CMD ["pnpm", "exec", "next", "dev", "--hostname", "0.0.0.0", "--port", "3000", "--webpack"]

# Production: the standalone server from the build stage. NEXT_PUBLIC_* values are baked in at
# build time, so pass them as build arguments.
FROM node:24-alpine@sha256:ebfe2f90462722a7a4de65e91990e97fe0d401c70e0e762c5b53302f905ec1c1 AS prod

WORKDIR /frontend

ENV NODE_ENV=production HOSTNAME=0.0.0.0 PORT=3000

# Owned by the image's unprivileged node user, which runs the server and writes Next's cache.
COPY --from=build --chown=node:node /frontend/.next/standalone ./
COPY --from=build --chown=node:node /frontend/.next/static ./.next/static
COPY --from=build --chown=node:node /frontend/public ./public

USER node

EXPOSE 3000

CMD ["node", "server.js"]
