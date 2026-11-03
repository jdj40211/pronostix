FROM python:3.11-alpine

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app.py pasarela.py ./

EXPOSE 5001
CMD ["gunicorn", "app:app", "--bind", "0.0.0.0:5001", "--workers", "2", "--access-logfile", "-"]
