FROM python:3.11-slim

WORKDIR /app

# Install dependencies
RUN pip install requests

# Copy the entire project
COPY . .

# Set environment variable for Python path
ENV PYTHONPATH=/app

# Default command (will be overridden in docker-compose)
CMD ["python", "edge/edge_server.py"]
