FROM python:3

WORKDIR /app

COPY app/ .
COPY data/ .

RUN pip install --no-cache-dir dnslib requests && \
    apt-get update && \
    apt-get install -y curl

EXPOSE 53/udp 53/tcp

CMD ["python", "dns_adblocker.py"]

