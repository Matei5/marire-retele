import socket
import logging
import time

logging.basicConfig(format=u'[LINE:%(lineno)d]# %(levelname)-8s [%(asctime)s] %(message)s', level=logging.INFO)

HOST = '0.0.0.0' # leaga pe toate interfetele din container
PORT = 10000

def handle_conn(conn, peer):
    # loop de primire/trimite pana cand clientul inchide conexiunea
    try:
        while True:
            data = conn.recv(1024) # citeste pana la 1024B
            if not data:
                logging.info("Client %s a închis conexiunea", peer)
                break
            logging.info('Primit de la %s: "%s"', peer, data.decode(errors='ignore'))
            reply = b"ACK:" + data
            conn.sendall(reply) # trimite raspunsul
    except Exception as e:
        logging.warning("Eroare pe conexiune %s: %s", peer, e)
    finally:
        conn.close()

sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM, proto=socket.IPPROTO_TCP)
sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
sock.bind((HOST, PORT))
logging.info("Serverul a pornit pe %s si portnul portul %d", HOST, PORT)
sock.listen(5)

try:
    while True:
        logging.info('Aștept conexiui...')
        conn, address = sock.accept()
        logging.info("Handshake cu %s", address)
        handle_conn(conn, address)
        time.sleep(1.0)
finally:
    sock.close()