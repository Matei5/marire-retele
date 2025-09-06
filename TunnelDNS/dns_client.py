import socket
import struct
import hashlib
import base64
import time
import sys
import os
import json
import random

TIMEOUT = 5.0
RETRIES = 3
DOWNLOAD_DIR = './downloads'
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

def encode_dns_name(name):
    out = b''
    for part in name.split('.'):
        if part:
            out += bytes([len(part)]) + part.encode('utf-8')
    return out + b'\x00'

def make_query(name):
    txid = random.randint(0, 0xFFFF)
    header = struct.pack('!HHHHHH', txid, 0x0100, 1, 0, 0, 0)  # RD=1
    question = encode_dns_name(name) + struct.pack('!HH', 16, 1)  # TXT IN
    return header + question, txid

def ask(server_ip, qname):
    pkt, txid = make_query(qname)
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.settimeout(TIMEOUT)
    try:
        s.sendto(pkt, (server_ip, 53))
        resp, _ = s.recvfrom(512)
        if len(resp) >= 2 and struct.unpack('!H', resp[:2])[0] == txid:
            return resp
        return None
    except Exception:
        return None
    finally:
        s.close()

def first_txt(resp):
    if not resp or len(resp) < 12:
        return None
    _, _, qd, an, _, _ = struct.unpack('!HHHHHH', resp[:12])
    off = 12
    for _ in range(qd):
        while off < len(resp):
            l = resp[off]
            if l == 0:
                off += 1
                break
            if l & 0xC0:
                off += 2
                break
            off += 1 + l
        off += 4
    for _ in range(an):
        if resp[off] & 0xC0:
            off += 2
        else:
            while resp[off] != 0:
                off += 1 + resp[off]
            off += 1
        rtype, _, _, rdlen = struct.unpack('!HHIH', resp[off:off+10])
        off += 10
        if rtype == 16:
            ln = resp[off]
            off += 1
            return resp[off:off+ln].decode('utf-8', 'strict')
        off += rdlen
    return None

def query_txt(server_ip, name):
    q = name.strip('.') + '.'
    for _ in range(RETRIES):
        resp = ask(server_ip, q)
        if resp:
            txt = first_txt(resp)
            if txt is not None:
                return txt
        time.sleep(1)
    return None

def download(server_ip, filename, domain):
    domain = domain.strip('.')
    info = query_txt(server_ip, f"info.{filename}.{domain}")
    if not info or ':' not in info:
        print("could not get info")
        return False
    total, expected_md5 = int(info.split(':', 1)[0]), info.split(':', 1)[1]
    print(f"meta: {total} chunks, md5 {expected_md5}")

    chunks_dir = os.path.join(DOWNLOAD_DIR, filename + ".chunks")
    state_path = os.path.join(DOWNLOAD_DIR, filename + ".state.json")
    final_path = os.path.join(DOWNLOAD_DIR, filename)
    os.makedirs(chunks_dir, exist_ok=True)

    state = {'downloaded': []}
    if os.path.isfile(state_path):
        try:
            with open(state_path, 'r') as f:
                state = json.load(f)
        except Exception:
            state = {'downloaded': []}
    done = set(state.get('downloaded', []))

    for i in range(total):
        if i in done and os.path.isfile(os.path.join(chunks_dir, str(i))):
            continue
        print(f"chunk {i+1}/{total}...", end=' ', flush=True)
        txt = query_txt(server_ip, f"{i}.{filename}.{domain}")
        if txt is None:
            print("fail")
            try:
                with open(state_path, 'w') as f:
                    json.dump(state, f)
            except Exception:
                pass
            return False
        try:
            with open(os.path.join(chunks_dir, str(i)), 'w') as f:
                f.write(txt)
        except Exception:
            print("fail")
            return False
        done.add(i)
        state['downloaded'] = sorted(done)
        try:
            with open(state_path, 'w') as f:
                json.dump(state, f)
        except Exception:
            pass
        print("ok")

    try:
        parts = []
        for i in range(total):
            with open(os.path.join(chunks_dir, str(i)), 'r') as f:
                parts.append(f.read())
        b64 = "".join(parts)
        data = base64.b64decode(b64)
    except Exception as e:
        print(f"assemble error: {e}")
        return False

    md5 = hashlib.md5(data).hexdigest()
    if md5 != expected_md5:
        print(f"md5 mismatch: expected {expected_md5}, got {md5}")
        return False
    try:
        with open(final_path, 'wb') as f:
            f.write(data)
    except Exception as e:
        print(f"save error: {e}")
        return False

    for i in range(total):
        try:
            os.remove(os.path.join(chunks_dir, str(i)))
        except OSError:
            pass
    try:
        os.remove(state_path)
    except OSError:
        pass
    try:
        os.rmdir(chunks_dir)
    except OSError:
        pass
    print(f"saved: {final_path} ({len(data)} bytes), md5 {md5}")
    return True

if len(sys.argv) < 3:
    print("usage: python3 dns_client.py <server_ip> <filename> [domain]")
    print("ex:    python3 dns_client.py 159.65.125.83 test.txt personalsubdomain.mooo.com")
    sys.exit(1)
server_ip = sys.argv[1]
filename = sys.argv[2]
domain = sys.argv[3] if len(sys.argv) > 3 else "personalsubdomain.mooo.com"
ok = download(server_ip, filename, domain)
sys.exit(0 if ok else 1)