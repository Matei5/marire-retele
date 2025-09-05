## ARP Spoofing 

RUN:

docker compose build --no-cache

docker compose up -d

docker compose exec -T middle tcpdump -A -s0 -n -i any tcp port 80 > http_dump.txt
docker compose exec server bash -lc 'wget -O- http://old.fmi.unibuc.ro | head'

CLOSE:

docker compose down -v --remove-orphans

CLEARING CACHE:

ip -s -s neigh flush all

arp -d 192.168.1.1
arp -n

OTHER:

docker compose exec -T middle tcpdump -n -i any tcp port 80 | tee capture.log
docker network ls
docker container prune -f
docker compose ps
docker compose logs -f middle


