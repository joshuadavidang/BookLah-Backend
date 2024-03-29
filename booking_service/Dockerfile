FROM python:3.12-slim
WORKDIR /usr/src/app
COPY requirements.txt ./
RUN python3 -m pip install --no-cache-dir -r requirements.txt
COPY ./dbConfig.py  .
COPY ./booking.py .
CMD [ "python", "./booking.py" ]