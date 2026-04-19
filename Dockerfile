# Use official lightweight Python image
FROM python:3.10-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file to the working directory
COPY backend/app/requirements.txt .

# Remove webdriver-manager and any selenium dependencies as per request 
# before installing the requirements
RUN sed -i '/webdriver-manager/d' requirements.txt && \
    sed -i '/selenium/d' requirements.txt && \
    pip install --no-cache-dir -r requirements.txt

# Copy only the backend/app directory (excluding core and web_scrape)
COPY backend/app /app/backend/app

# Set the working directory to the app folder so uvicorn can find main.py
WORKDIR /app/backend/app

# Expose port
EXPOSE 8000

# Start the FastAPI application with Uvicorn, using the PORT env variable provided by Render
CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}"]
