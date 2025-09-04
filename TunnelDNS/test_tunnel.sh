#!/bin/bash
# Script pentru testarea tunelului DNS

echo "=== Test DNS Tunnel ==="
echo

# Verificam daca fisierele exist
if [ ! -f "dns_server.py" ] || [ ! -f "dns_client.py" ]; then
    echo "Eroare: Fisierele server/client nu exista!"
    exit 1
fi

# Facem fisierele executabile
chmod +x dns_server.py dns_client.py

echo "1. Pornesc serverul DNS in background..."
python3 dns_server.py &
SERVER_PID=$!

echo "   Server PID: $SERVER_PID"
sleep 2

echo
echo "2. Testez conectivitatea cu dig..."
dig @localhost info.test.tunel.live TXT

echo
echo "3. Testez clientul DNS..."
python3 dns_client.py localhost test.txt

echo
echo "4. Verific MD5 checksum..."
if [ -f "downloads/test.txt" ] && [ -f "server_files/test.txt" ]; then
    echo "Original:"
    md5sum server_files/test.txt
    echo "Descarcat:"
    md5sum downloads/test.txt
    
    if md5sum -c <(md5sum server_files/test.txt | sed 's/server_files/downloads/') 2>/dev/null; then
        echo "✓ MD5 checksum-urile coincid!"
    else
        echo "✗ MD5 checksum-urile NU coincid!"
    fi
else
    echo "Fisierele nu exista pentru verificare."
fi

echo
echo "5. Opresc serverul..."
kill $SERVER_PID 2>/dev/null

echo "Test complet!"
