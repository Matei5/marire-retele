# TCP Hijacking 

## RUN:

docker compose build --no-cache
docker compose up -d

docker compose exec server bash -lc 'python3 /app/tcp-server.py'
docker compose exec router bash -lc 'iptables -I FORWARD -p tcp --dport 10000 -j NFQUEUE --queue-num 1; iptables -I FORWARD -p tcp --sport 10000 -j NFQUEUE --queue-num 1; python3 /app/tcp-middle.py'
docker compose exec client bash -lc "echo '172.29.0.10 server' >> /etc/hosts; python3 /app/tcp-client.py"

## CLOSE:

docker compose down -v --remove-orphans

## OTHER:

docker compose ps

## Clearing cache:

ip -s -s neigh flush all

arp -d 192.168.1.1
arp -n