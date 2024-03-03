FROM python:3.12-slim
WORKDIR /usr/src/app
COPY requirements.txt ./
RUN python -m pip install --no-cache-dir -r requirements.txt
COPY ./book.py .
CMD [ "python", "./booking.py" ]