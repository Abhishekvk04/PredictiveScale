FROM python:3.10-slim
WORKDIR /app
COPY actuator.py /app/actuator.py
RUN pip install --no-cache-dir requests kubernetes
CMD ["python","/app/actuator.py"]
