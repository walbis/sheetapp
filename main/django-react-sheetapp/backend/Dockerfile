# Use an official Python runtime as a parent image
FROM python:3.11-slim

# Set environment variables to prevent Python from writing pyc files and buffering stdout/stderr
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Set the working directory in the container
WORKDIR /code

# Install system dependencies required for psycopg2 (PostgreSQL adapter) and potentially other libraries
# Using --no-install-recommends reduces image size
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    # Add other system dependencies if needed (e.g., for image processing like libjpeg-dev)
    && rm -rf /var/lib/apt/lists/*

# Install pip dependencies
# Copy requirements first to leverage Docker cache
COPY requirements.txt /code/
# Consider using --no-cache-dir for slightly smaller image size in production
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# Copy the rest of the application code into the container
COPY . /code/

# Expose the port the app runs on (defined in docker-compose.yml as well)
EXPOSE 8000

# Define the command to run the application
# For development, use the Django development server
# For production, use a production-grade WSGI server like Gunicorn or uWSGI
# Example Production command (uncomment and adjust if needed):
# CMD ["gunicorn", "project_config.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "4"]
# Development command (used by default docker-compose):
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]