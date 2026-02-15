FROM python:3.13-slim

WORKDIR /srv

# Install xycore first (local dependency, not on PyPI)
COPY packages/xycore packages/xycore
RUN pip install --no-cache-dir packages/xycore

# Install API with production dependencies
COPY apps/api apps/api
RUN pip install --no-cache-dir "apps/api[prod]"

WORKDIR /srv/apps/api

COPY apps/api/entrypoint.sh /srv/entrypoint.sh
RUN chmod +x /srv/entrypoint.sh

ENV PORT=8000
EXPOSE 8000
ENTRYPOINT ["/srv/entrypoint.sh"]
