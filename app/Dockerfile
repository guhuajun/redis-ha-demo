FROM python:3-alpine

WORKDIR /app/
COPY requirements.txt .

RUN pip install -r requirements.txt \
        --index-url http://mirrors.aliyun.com/pypi/simple/ \
        --trusted-host mirrors.aliyun.com

COPY app.py .

CMD ["python", "app.py"]
