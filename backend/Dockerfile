FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .

ENV DB_PATH=/data/students.db
EXPOSE 8000

# Single worker is fine for a small school deployment. For more load, put
# gunicorn in front: CMD ["gunicorn","-b","0.0.0.0:8000","app:app"]
CMD ["python", "app.py"]
