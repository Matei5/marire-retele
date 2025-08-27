import socket
import os
from datetime import datetime
from dnslib import DNSRecord, RR, QTYPE, A

# load blocked domains
blocklist = []
try:
    f = open("blocklist.txt")
    for line in f:
        line = line.strip()
        if line and not line.startswith("#"):
            parts = line.split()
            if len(parts) == 2 and parts[0] == "0.0.0.0":
                blocklist.append(parts[1].lower())
    f.close()
    print("loaded", len(blocklist), "domains")
except Exception as e:
    print(f"Error loading blocklist: {e}")
    blocklist = []

# Create data directory if it doesn't exist
os.makedirs("../data", exist_ok=True)
LOG_FILE = "../data/blocked_domains.log"

# dns server
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) #IPv4, UDP
sock.bind(("0.0.0.0", 53))
print("DNS server started on 0.0.0.0:53")

while True:
    try:
        data, addr = sock.recvfrom(512)
        
        # parse dns request
        request = DNSRecord.parse(data)
        qname = str(request.q.qname).rstrip('.').lower() # q = question of packet, qname = site name
        print(f"query: {qname} from {addr}")
        
        # check if blocked
        blocked = False
        for domain in blocklist:
            if qname == domain or qname.endswith("." + domain):
                blocked = True
                break
        
        if blocked:
            # send blocked response
            reply = request.reply()
            reply.add_answer(RR(qname, QTYPE.A, rdata=A("0.0.0.0"), ttl=60)) # A record with IPv4, cache for 60 seconds
            sock.sendto(reply.pack(), addr)
            
            # log blocked domain
            try:
                with open(LOG_FILE, "a") as logfile:
                    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    logfile.write(f"{timestamp} - {qname}\n")
                    logfile.flush()  # Ensure immediate write
            except Exception as e:
                print(f"Error logging: {e}")
            
            print("BLOCKED:", qname)
        else:
            # forward to Google DNS
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                s.settimeout(3)
                s.sendto(data, ("8.8.8.8", 53))
                resp, _ = s.recvfrom(4096)
                sock.sendto(resp, addr)
                s.close()
                print("forwarded:", qname)
            except Exception as e:
                print(f"Failed to forward {qname}: {e}")
                # Send a simple error response if forwarding fails
                reply = request.reply()
                reply.header.rcode = 2  # Server failure
                sock.sendto(reply.pack(), addr)
                
    except Exception as e:
        print(f"Error processing DNS request: {e}")
        continue
