FROM python:3.12-slim
WORKDIR /usr/src/app
COPY requirements.txt ./
RUN python3 -m pip install --no-cache-dir -r requirements.txt
COPY ./amqp_connection.py .
COPY ./admin.py .
COPY ./invokes.py .
CMD [ "python3", "admin.py" ]
