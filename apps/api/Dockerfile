FROM python:3.13-slim

WORKDIR /srv

# Install xycore first (local dependency, not on PyPI)
COPY packages/xycore packages/xycore
RUN pip install --no-cache-dir packages/xycore

# Install API with production dependencies
COPY apps/api apps/api
RUN pip install --no-cache-dir "apps/api[prod]"

WORKDIR /srv/apps/api

ENV PORT=8000
EXPOSE ${PORT}
CMD uvicorn app.main:app --host 0.0.0.0 --port ${PORT} --workers 4
