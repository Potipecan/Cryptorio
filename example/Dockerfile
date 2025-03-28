FROM python:3.11
LABEL authors="poti"
LABEL maintainer="andraz.podpecan1@student.um.si"


WORKDIR /kafka-example
COPY requirements.txt requirements.txt
COPY kafka_interface.py kafka_interface.py
RUN pip install -r requirements.txt

CMD ["python3", "kafka_interface.py", "-i", "ping"]