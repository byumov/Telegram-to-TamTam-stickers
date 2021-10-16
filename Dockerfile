FROM python:3.9.7
COPY / /app
EXPOSE 19999
RUN pip3 install -r /app/requirements.txt
ENTRYPOINT [ "python", "/app/main.py" ]
