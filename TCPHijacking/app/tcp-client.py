import socket
import logging
import time

logging.basicConfig( format=u'[LINE:%(lineno)d]# %(levelname)-8s [%(asctime)s] %(message)s', level=logging.INFO)

HOST = 'server'   # hostname DNS al serverului din docker-compose.yml
PORT = 10000

while True:
    sock = None
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM, proto=socket.IPPROTO_TCP)
        server_address = (HOST, PORT)
        logging.info('Handshake cu %s', server_address)
        sock.connect(server_address)

        while True:
            mesaj = "MSG:---STATIC---"
            sock.sendall(mesaj.encode('utf-8'))
            data = sock.recv(1024)
            logging.info('Răspuns primit: "%s"', data.decode(errors='ignore'))
            time.sleep(1.0)

    except Exception as e:
        logging.warning("Problema conexiunii: %s. Reîncerc în 1s.", e)
        time.sleep(1.0)
    finally:
        logging.info('closing socket')
        sock.close()

