FROM gcr.io/deeplearning-platform-release/pytorch-gpu

RUN pip install --no-cache-dir transformers==4.30.0 Pillow==9.5.0 uvicorn==0.14.0 gunicorn==20.0.4

COPY app.py ./app.py
COPY ./model /model

EXPOSE 8080


CMD ["gunicorn", "-b", "0.0.0.0:8080","app:app","--workers","1","-k","uvicorn.workers.UvicornWorker"]