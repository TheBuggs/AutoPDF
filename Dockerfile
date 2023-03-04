FROM python:3.10.2-slim-buster

WORKDIR /usr/src/app

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

RUN apt-get update && apt-get install -y \
    imagemagick ffmpeg libsm6 libxext6 poppler-utils \
    sqlite3 libsqlite3-dev tesseract-ocr \
    libtesseract-dev libleptonica-dev

RUN /usr/bin/sqlite3 /project/db/db.db

RUN pip install --upgrade pip

COPY ./requirements.txt .

RUN pip install -r requirements.txt

COPY . .
