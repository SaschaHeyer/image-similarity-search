FROM python:3.11-slim
ENV PYTHONUNBUFFERED True

RUN pip install vertexai==1.49.0 Flask==2.3.2 gunicorn==20.1.0 requests==2.31.0 google-cloud-storage==2.9.0

ENV APP_HOME /app
WORKDIR $APP_HOME
COPY . ./

CMD exec gunicorn --bind :$PORT --workers 1 --threads 8 --timeout 0 main:app