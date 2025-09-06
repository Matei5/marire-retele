#!/usr/bin/env python3
from netfilterqueue import NetfilterQueue
from scapy.all import IP, TCP, Raw
import logging

logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(message)s')

TARGET_PORT = 10000
MARKER = b"[INJECTAT]|" 

def should_touch(tcp: TCP) -> bool:
    # Verifica daca se uita la portul dorit
    return tcp.dport == TARGET_PORT or tcp.sport == TARGET_PORT

def inject_same_len(orig: bytes) -> bytes:
    if not orig:
        return orig
    need = len(MARKER)
    if len(orig) <= need:
        return orig
    return MARKER + orig[:len(orig) - need]

def process(nfpacket):
    try:
        pkt = IP(nfpacket.get_payload())
    except Exception as e:
        logging.error("Nu pot parsa pachetul: %s", e)
        return nfpacket.accept()

    # Verifica IP/TCP + daca exista date in pachet
    if pkt.haslayer(TCP) and pkt.haslayer(Raw):
        tcp = pkt[TCP]
        if should_touch(tcp) and (tcp.flags & 0x08):  # 0x08 = PSH
            orig = bytes(pkt[Raw].load)
            new_payload = inject_same_len(orig)
            if new_payload != orig:
                # Inlocuieste payload-ul pastrand aceeasi lungime
                pkt[Raw].load = new_payload
                for fld in ("len", "chksum"):
                    if hasattr(pkt[IP], fld):
                        try:
                            delattr(pkt[IP], fld)
                        except Exception:
                            pass
                try:
                    del pkt[TCP].chksum
                except Exception:
                    pass

                nfpacket.set_payload(bytes(pkt))
                logging.info(
                    "Injectat %s:%d -> %s:%d (len=%d)",
                    pkt[IP].src, tcp.sport, pkt[IP].dst, tcp.dport, len(orig)
                )

    return nfpacket.accept()

nfq = NetfilterQueue()
try:
    logging.info("Atașare la NFQUEUE 1…")
    nfq.bind(1, process)
    logging.info("Running...")
    nfq.run()
finally:
    nfq.unbind()
