## TCP Hijacking 

Clearing cache:

ip -s -s neigh flush all

arp -d 192.168.1.1
arp -n

RUN:

docker compose build --no-cache

docker compose up -d

docker compose ps
docker compose logs -f middle

Rulare (in containerul middle / router cu iptables pregatit):
    iptables -I FORWARD -p tcp --dport 10000 -j NFQUEUE --queue-num 1
    iptables -I FORWARD -p tcp --sport 10000 -j NFQUEUE --queue-num 1
    python3 /app/tcp_hijack.py

Ce face:
    - Intercepteaza pachete TCP cu payload pe portul 10000
    - Daca pachetul are date (PSH) le inlocuieste cu un mesaj HIJACKED (trunchiat/padding la aceeasi dimensiune)
    - Recalculeaza checksum automat (prin stergerea campurilor)

Avantaj: lungimea identica => niciun impact asupra stream-ului din perspectiva endpoint-urilor.