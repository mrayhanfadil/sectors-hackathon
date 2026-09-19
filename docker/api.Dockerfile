# syntax=docker/dockerfile:1.7
# API + PDF renderer.
#
# The base image is the point of this file: the deck is rendered by Chromium through Playwright, so the image ships the
# browser build that matches the library version instead of downloading ~1 GB inside the build. Keep the tag in step
# with `playwright` in server/requirements.txt - a mismatch is a runtime error, not a warning.
FROM mcr.microsoft.com/playwright/python:v1.60.0-noble

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=0

WORKDIR /app

# 1. Dependencies first, source later. This is what makes a rebuild after a code change take seconds: the install
#    layer is only invalidated when a manifest changes. The cache mount keeps pip's download cache between builds, so
#    even a manifest change does not re-download the wheels.
COPY server/requirements.txt /tmp/req-server.txt
COPY agents/adk/requirements.txt /tmp/req-adk.txt

# The report and PDF path needs only the server requirements (the critic imports stdlib and the repo's own formatter).
# The Google ADK stack is needed by the /agent routes alone, so it is a build arg: WITH_ADK=false gives a slim image
# for report-only use, the default keeps every route working.
ARG WITH_ADK=true
RUN --mount=type=cache,target=/root/.cache/pip,sharing=locked \
    pip install -r /tmp/req-server.txt && \
    if [ "$WITH_ADK" = "true" ]; then pip install -r /tmp/req-adk.txt; fi

# 2. House typography. The deck is set in the fonts shipped in the repository; without them the PDF silently falls
#    back to whatever the base image has and the pages no longer look like the deck. Roboto is the Sectoral body
#    face, so a build that cannot see it must say so loudly rather than ship Liberation Sans under a Roboto stack.
COPY assets/fonts/ /usr/share/fonts/truetype/house/
RUN fc-cache -f >/dev/null \
    && fc-list | grep -ci "ibm plex\|source serif\|jetbrains" | sed 's/^/house fonts installed: /' \
    && fc-list | grep -ci "roboto" | sed 's/^/roboto faces installed: /' \
    && test "$(fc-list | grep -ci 'roboto')" -ge 6 \
    || { echo "FAIL: Roboto not visible to fontconfig. assets/fonts/*.ttf is gitignored - run 'python scripts/fetch_house_fonts.py' and rebuild."; exit 1; }

# 3. The base image ships three browsers (~3.4 GB); the app launches chromium only (server/routers/pdf.py). Dropping
#    firefox and webkit takes about a gigabyte off the image and costs nothing, because nothing can reach for them.
RUN rm -rf /ms-playwright/firefox* /ms-playwright/webkit* /ms-playwright/ffmpeg* \
    && du -sh /ms-playwright | sed 's/^/browsers kept: /'

# 4. Application source. Last, because it changes most often.
COPY . .

# data/ and output/ are mounted in compose: assumptions stay editable on the host and the harvest cache survives a
# container rebuild. Creating them here keeps the image runnable on its own.
RUN mkdir -p /app/data /app/output

EXPOSE 8777

# /api/health is cheap (it reports cache and provider state) and does not render a report, so it is safe to poll.
HEALTHCHECK --interval=30s --timeout=10s --start-period=25s --retries=3 \
    CMD python -c "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8777/api/health', timeout=8).status == 200 else 1)"

# Same entrypoint as the systemd unit on the host, so the container and the service cannot drift.
CMD ["python", "-m", "uvicorn", "server.main:app", "--host", "0.0.0.0", "--port", "8777"]
