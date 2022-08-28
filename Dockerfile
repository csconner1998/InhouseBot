FROM python:3.8-slim-buster

# psycopg2 requirement lib on linux
RUN apt-get update \
    && apt-get -y install libpq-dev gcc

WORKDIR /bot

# Copy files to work directory
COPY bot.py ./
COPY ./inhouse ./inhouse
COPY requirements.txt .

RUN pip3 install -r requirements.txt

EXPOSE 443

CMD [ "python3", "bot.py" ]