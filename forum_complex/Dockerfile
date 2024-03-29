FROM python:3.12-slim
WORKDIR /usr/src/app
COPY requirements.txt ./
RUN python3 -m pip install --no-cache-dir -r requirements.txt
COPY ./amqp_setup.py .
COPY ./forum_complex.py .
COPY ./invokes.py .
RUN ./amqp_setup.py
CMD [ "python3", "./forum_complex.py" ]