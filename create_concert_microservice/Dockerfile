FROM python:3.12-slim
WORKDIR /usr/src/app
COPY requirements.txt ./
RUN python3 -m pip install --no-cache-dir -r requirements.txt
COPY ./amqp_connection.py .
COPY ./create_concert.py .
COPY ./invokes.py .
CMD [ "python3", "create_concert.py" ]
