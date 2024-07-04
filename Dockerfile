FROM python:3.12-bookworm

WORKDIR /usr/src/app

COPY requirements.txt ./
RUN pip3 install --no-cache-dir -r requirements.txt

COPY . .

CMD [ "python3", "./sensor-service.py" ]
