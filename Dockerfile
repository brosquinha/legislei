FROM python:3.7-alpine

LABEL maintainer="Thales César Giriboni <thalesgiriboni@gmail.com>"

RUN apk add tzdata

RUN cp /usr/share/zoneinfo/America/Sao_Paulo /etc/localtime

# We copy just the requirements.txt first to leverage Docker cache
COPY ./requirements.txt /app/requirements.txt

WORKDIR /app

RUN pip3 install -r requirements.txt

COPY . /app

ENTRYPOINT [ "python3" ]

CMD [ "run.py" ]