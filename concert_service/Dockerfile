FROM python:3-slim
WORKDIR /usr/src/app
COPY requirements.txt ./
RUN python3 -m pip install --no-cache-dir -r requirements.txt
COPY ./dbConfig.py  .
COPY ./concerts.py  .
CMD ["python3", "concerts.py"]