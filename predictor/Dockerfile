FROM python:3.10-slim
WORKDIR /app
COPY model.pkl /app/model.pkl
COPY app.py /app/app.py
RUN pip install --no-cache-dir fastapi uvicorn requests scikit-learn numpy prometheus_client
EXPOSE 8000 8001
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
