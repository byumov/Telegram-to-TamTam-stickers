FROM python:3.9.7-alpine
RUN apk --no-cache add gcc musl-dev libffi-dev libwebp-dev zlib-dev jpeg-dev
COPY ./requirements.txt /app/requirements.txt
WORKDIR /app
RUN pip install -r requirements.txt
ADD . /app
RUN python setup.py sdist
RUN pip install dist/*
EXPOSE 19999
ENTRYPOINT [ "tg-to-tt-bot" ]
