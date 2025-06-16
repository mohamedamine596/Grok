FROM python:3.10-slim

WORKDIR /app

# Copy requirements first for better layer caching
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Install additional dependencies
RUN pip install openai requests pillow flask

# Copy the rest of the application code
COPY . .

# Create output directory for generated images
RUN mkdir -p /app/generated_images

# Expose port 8081 for the API
EXPOSE 8081

# Set environment variables
ENV PYTHONUNBUFFERED=1

# Start the API server
CMD ["python", "main.py", "api"]
