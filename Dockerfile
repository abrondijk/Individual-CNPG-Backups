# Base image
FROM python:3.12.8-alpine3.21

# Set the working directory inside the container
WORKDIR /app

# Install system packages
RUN apk add --no-cache \
    postgresql16

# Copy the python script into the container
COPY src/main.py ./main.py

# Install Python packages from requirements.txt
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Specify the Python script to run as the entry point
ENTRYPOINT ["python", "main.py"]
