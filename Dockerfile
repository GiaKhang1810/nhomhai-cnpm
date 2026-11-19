# Libra - Flask application container
FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    POETRY_VIRTUALENVS_CREATE=false \
    POETRY_NO_INTERACTION=1

WORKDIR /app

# Install locked project dependencies.
RUN pip install --no-cache-dir "poetry>=2.0,<3.0"
COPY pyproject.toml poetry.lock ./
RUN poetry install --only main --no-root --no-ansi

# Copy the application after dependency installation to keep Docker cache useful.
COPY source/ ./source/
COPY scripts/ ./scripts/

# The Flask application must bind to all interfaces inside the container.
EXPOSE 5000

# The built-in Flask server is suitable for coursework/demo deployment.
# For production use a dedicated WSGI server behind a reverse proxy.
CMD ["flask", "--app", "source.app:create_app", "run", "--host=0.0.0.0", "--port=5000", "--no-debugger"]
