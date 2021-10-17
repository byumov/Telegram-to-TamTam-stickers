FROM python:3.9.7 AS build
COPY / /app
WORKDIR /app
RUN python setup.py sdist

FROM python:3.9.7-alpine
COPY --from=build /app/dist /dist
RUN apk --no-cache add gcc musl-dev libffi-dev libwebp-dev zlib-dev jpeg-dev
RUN pip install /dist/*
EXPOSE 19999
ENTRYPOINT [ "tg-to-tt-bot" ]
