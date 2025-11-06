FROM python:3.13-bookworm

ADD requirements.txt /app/requirements.txt
RUN pip install -r /app/requirements.txt

WORKDIR /app/src
ADD indexing_provider.py /app/src/

ENTRYPOINT ["python", "indexing_provider.py"]
