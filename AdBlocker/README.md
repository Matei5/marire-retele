## Run

docker build -t dns:latest .

sudo systemctl stop systemd-resolved
sudo systemctl disable systemd-resolved
docker compose up -d

Troubleshoot: docker compose restart

Modify files from old ip to new ip:

cat /etc/resolv.conf
sudo cp /etc/resolv.conf /etc/resolv.conf.backup
sudo rm /etc/resolv.conf
echo "nameserver 127.0.0.1" | sudo tee /etc/resolv.conf

## Close - A lot of commands to make sure everything works afterwards

docker compose down

sudo cp /etc/resolv.conf.backup /etc/resolv.conf

sudo systemctl enable systemd-resolved
sudo systemctl start systemd-resolved

sudo resolvectl revert wlp9s0
sudo systemctl restart systemd-resolved

sudo rm /etc/resolv.conf.backup

# Stats

python app/domain_statistics.py

sudo ss -ulpn | grep ':53'    # UDP
sudo ss -tlpn | grep ':53'    # TCP

# Upon system restart

sudo systemctl stop systemd-resolved
sudo systemctl disable systemd-resolved
docker compose restart