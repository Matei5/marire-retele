## Run

sudo systemctl stop systemd-resolved

docker compose up -d

## Close

docker compose down

sudo systemctl start systemd-resolved

sudo resolvectl revert wlp9s0

sudo systemctl restart systemd-resolved

# Stats

python app/domain_statistics.py

