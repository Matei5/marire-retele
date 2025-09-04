cd /opt/marire-retele/TunnelDNS
sudo -E python3 dns_server.py

python3 dns_client.py 159.65.125.83 test.txt t.mytini.live

md5sum downloads/test.txt


-- After test:

Server:

root@VPS:/opt/marire-retele/TunnelDNS# sudo -E python3 dns_server.py
DNS tunnel server started on 0.0.0.0:53

Client:

matei@matei-LOQ-15IRH8:~/Documents/2. Projects/marire-retele/TunnelDNS$ python3 dns_client.py 159.65.125.83 test.txt t.mytini.live
meta: 4 chunks, md5 06922c340fc41b7847567d7147d68404
chunk 1/4... ok
chunk 2/4... ok
chunk 3/4... ok
chunk 4/4... ok
saved: ./downloads/test.txt (467 bytes), md5 06922c340fc41b7847567d7147d68404
matei@matei-LOQ-15IRH8:~/Documents/2. Projects/marire-retele/TunnelDNS$ md5sum downloads/test.txt
06922c340fc41b7847567d7147d68404  downloads/test.txt