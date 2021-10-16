FROM python:3.9.7 AS build
COPY / /app
WORKDIR /app
RUN python setup.py sdist

FROM python:3.9.7
COPY --from=build /app/dist /dist
WORKDIR /app
EXPOSE 19999
RUN pip install /dist/*
ENTRYPOINT [ "tg-to-tt-bot" ]
