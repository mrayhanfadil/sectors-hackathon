# syntax=docker/dockerfile:1.7
# Front-end, built here and served by nginx from the same origin as the API.
#
# VITE_API_URL is deliberately empty: the app falls back to a relative base (src/fe/src/lib/api.ts), and nginx proxies
# /api to the api service. One origin means no CORS, and the same build works behind any hostname.

FROM node:22-alpine AS build
WORKDIR /fe

# Manifest first, source second: npm ci only re-runs when the lockfile moves, and the cache mount keeps the tarballs
# between builds so even that is fast.
COPY src/fe/package.json src/fe/package-lock.json ./
RUN --mount=type=cache,target=/root/.npm,sharing=locked npm ci

COPY src/fe/ ./
ARG VITE_API_URL=""
ENV VITE_API_URL=$VITE_API_URL
RUN npm run build


FROM nginx:1.27-alpine AS runtime
# The SPA is content-hashed by Vite, so long-lived caching is safe and the config says so explicitly.
COPY docker/nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /fe/dist /usr/share/nginx/html

EXPOSE 80
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD wget -q -O /dev/null http://127.0.0.1/ || exit 1

CMD ["nginx", "-g", "daemon off;"]
