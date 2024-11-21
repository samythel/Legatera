FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8080

CMD ["python3", "-m", "gunicorn", "--bind=0.0.0.0:8080", "--workers=4", "--timeout=0", "app:app"]
