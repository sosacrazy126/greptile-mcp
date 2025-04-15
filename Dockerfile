# Use an official Python runtime as a parent image
FROM python:3.9-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    # Set default host and port, can be overridden by --env-file or -e flags in docker run
    HOST=0.0.0.0 \
    PORT=8050 \
    # Set default Greptile URL, can be overridden
    GREPTILE_BASE_URL=https://api.greptile.com/v2

# Argument for build-time port configuration (optional, ENV PORT is usually sufficient)
ARG PORT=8050

# Set the working directory in the container
WORKDIR /app

# Copy the dependencies file
COPY pyproject.toml README.md ./

# Install dependencies using pip and the pyproject.toml file
# Using --no-cache-dir reduces image size
RUN pip install --no-cache-dir -e .

# Copy the application code
COPY ./src ./src

# Make port ${PORT} available outside this container
EXPOSE ${PORT}

# Define the command to run the application
CMD ["python", "-m", "src.main"] 