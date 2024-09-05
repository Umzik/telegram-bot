# Use an official Python runtime as a parent image
FROM python:3.10-slim

# Set the working directory in the container
WORKDIR /app

# Copy the requirements.txt to the container at /app
COPY requirements.txt /app/

# Install any dependencies specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the current directory contents into the container at /app
COPY . /app/

# Set environment variables for Django backend URL (modify this as needed)
ENV DJANGO_BACKEND_URL=http://web:8000/api

# Expose the port (if your bot listens on a specific port, e.g., for webhook setup)
# EXPOSE 8443 (for webhooks if necessary)

# Run the bot
CMD ["python", "main.py"]
