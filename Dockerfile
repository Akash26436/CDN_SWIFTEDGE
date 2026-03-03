FROM python:3.11
WORKDIR /app
COPY . .
RUN pip install requests
ENV PYTHONPATH=/app/edge
CMD ["python", "edge/edge_server.py", "--port", "8081"]
