FROM python:3.12-slim

ARG TARGETARCH

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Create a user and group
RUN addgroup --gid 1000 appgroup && adduser --uid 1000 --gid 1000 --disabled-password appuser

# Set the working directory in the container to /app
WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
  build-essential \
  gcc \
  libpq-dev \
  libc6-dev \
  && apt-get clean \
  && rm -rf /var/lib/apt/lists/*

# Copy entrypoint.sh and requirements.txt into the container at /app
COPY entrypoint.sh requirements.txt /app/

# Ensure the entrypoint script is executable
RUN chmod a+x /app/entrypoint.sh

# Install any needed packages specified in requirements.txt
RUN pip install --upgrade pip \
  && pip install --no-cache-dir -r /app/requirements.txt

# Establish the rights to the directory
RUN mkdir -p /app/sessions && chown -R appuser:appgroup /app/sessions

# Copy the current directory source code
COPY src/ /app/

# Switching to an unheard of user
USER 1000

# Run the telegram bot
ENTRYPOINT ["/app/entrypoint.sh"]
CMD []
