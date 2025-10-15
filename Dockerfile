FROM python:3.11-alpine

VOLUME /app
WORKDIR /app
RUN mkdir /app/src
ADD requirements.txt .

EXPOSE 5000

RUN pip3 install -r requirements.txt
CMD python -m flask --app src/app.py run --debug --host=0.0.0.0
