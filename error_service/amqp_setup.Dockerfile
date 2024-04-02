# Use an appropriate base image with Python installed

FROM python:3-slim

# Set the working directory in the container
WORKDIR /usr/src/app

# Copy the amqp_setup.py script into the container
COPY amqp_setup.py /amqp_setup.py

# Install any dependencies required by the script (if any)
# For example, if your script uses the pika library, you can install it like this:
RUN python -m pip install --no-cache-dir -r requirements.txt

# Run the script using the Python interpreter
CMD ["python", "amqp_setup.py"]
