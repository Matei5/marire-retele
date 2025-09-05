# Tunel DNS

## Comenzi folosite

### Install necessery packages
sudo apt-get update
sudo apt-get install -y python3 python3-venv python3-pip dnsutils \
                        netfilter-persistent iptables-persistent

### Free port 53:
sudo sed -i 's/^#\?DNSStubListener=.*/DNSStubListener=no/' /etc/systemd/resolved.conf 
sudo systemctl restart systemd-resolved

### Iptables setup
sudo iptables -I INPUT -p udp --dport 53 -j ACCEPT
sudo iptables -I INPUT -m state --state NEW -p tcp --dport 8080 -j ACCEPT
sudo netfilter-persistent save

### Verify rules:
sudo iptables -L INPUT -n -v --line-numbers
sudo iptables-save | grep -E 'dport (53|8080)'

### Run
cd /opt/marire-retele/TunnelDNS
sudo -E python3 dns_server.py

python3 dns_client.py 159.65.125.83 test.txt t.mytini.live

md5sum downloads/test.txt


### Test example:

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