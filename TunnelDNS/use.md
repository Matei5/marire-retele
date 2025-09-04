cd /opt/marire-retele/TunnelDNS
sudo -E python3 dns_server.py

python3 dns_client.py 159.65.125.83 test.txt t.mytini.live

md5sum downloads/test.txt
