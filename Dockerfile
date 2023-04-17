FROM python:3.9

WORKDIR /app
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY mdns_search.py ./
COPY vestasync.py ./
COPY files files/
CMD ["python", "vestasync.py"]
