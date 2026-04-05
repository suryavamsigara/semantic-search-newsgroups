# Use a lightweight Python 3.12 image
FROM python:3.12-slim

# Copy the uv installer from the official astral image
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Set the working directory inside the container
WORKDIR /app

# Copy the dependency files first to utilize Docker layer caching
COPY pyproject.toml uv.lock ./

# Install dependencies strictly according to the lockfile (no dev dependencies)
RUN uv sync --frozen --no-dev

# Copy the rest of the backend files (including the db folder and your python scripts)
COPY . .

# Expose the port that FastAPI will run on
EXPOSE 8000

# Start the application using uv to run uvicorn
CMD ["uv", "run", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]