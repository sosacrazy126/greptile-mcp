# Use an official Python runtime as a parent image
FROM python:3.11-slim

# Set the working directory in the container
WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY src/ ./src/

# Set default environment variables
ENV PYTHONUNBUFFERED=1 \
    GREPTILE_BASE_URL=https://api.greptile.com/v2 \
    HOST=0.0.0.0 \
    PORT=8080

# Default to SSE transport, can be overridden by Smithery
ENV TRANSPORT=sse

# Make port ${PORT} available outside this container
EXPOSE ${PORT}

# Define the command to run the application
CMD ["python", "-m", "src.main"] 