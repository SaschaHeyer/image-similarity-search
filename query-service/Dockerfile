FROM tiangolo/uvicorn-gunicorn-fastapi:python3.8-slim
RUN pip install --no-cache-dir requests==2.31.0 google-cloud-aiplatform==1.59.0
COPY app.py ./app.py

CMD ["gunicorn", "-b", "0.0.0.0:8080","app:app","-k","uvicorn.workers.UvicornWorker","--timeout", "0"]