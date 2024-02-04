FROM debian:sid

# Use a valid Debian Sid repository mirror
RUN echo 'deb http://deb.debian.org/debian sid main contrib non-free' > /etc/apt/sources.list

# Update package lists and upgrade existing packages
RUN apt update && apt upgrade -y
RUN apt-get install tzdata -y
# Install necessary dependencies
RUN apt install -y python3 python3-dev python3-pip python3-venv npm git

# Create a virtual environment and install required Python packages
RUN python3 -m venv /venv
ENV PYTHON=/venv/bin/python3
RUN $PYTHON -m pip install poetry gunicorn

# Set working directory
WORKDIR /app

# Copy only the dependency files to leverage Docker cache
COPY poetry.lock pyproject.toml /app/
RUN $PYTHON -m poetry config virtualenvs.create false && $PYTHON -m poetry install --no-interaction --only main

# Copy the entire application code
COPY . /app

# Make port 5500 available to the world outside this container
EXPOSE 5500

# Run the application using gunicorn
CMD ["/venv/bin/python3", "app.py"]
