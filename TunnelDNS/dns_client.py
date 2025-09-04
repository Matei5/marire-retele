#!/usr/bin/env python3
import socket
import struct
import hashlib
import base64
import time
import sys
import os
import json

# Configuration
TIMEOUT = 5.0
MAX_RETRIES = 3
DOWNLOAD_DIR = './downloads'
CHUNK_DIR_SUFFIX = '.chunks'
STATE_SUFFIX = '.state.json'

os.makedirs(DOWNLOAD_DIR, exist_ok=True)

def encode_dns_name(name):
    encoded = b''
    for part in name.split('.'):
        if part:
            encoded += struct.pack('!B', len(part)) + part.encode('utf-8')
    encoded += b'\x00'
    return encoded

def send_dns_query(query_name, query_type, server_ip, server_port=53):
    transaction_id = int(time.time()) & 0xFFFF
    flags = 0x0100
    header = struct.pack('!HHHHHH', transaction_id, flags, 1, 0, 0, 0)
    question = encode_dns_name(query_name) + struct.pack('!HH', query_type, 1)
    query_packet = header + question
    
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.settimeout(TIMEOUT)
    
    try:
        sock.sendto(query_packet, (server_ip, server_port))
        response, _ = sock.recvfrom(512)
        response_id = struct.unpack('!H', response[:2])[0]
        if response_id == transaction_id:
            return response
    except:
        pass
    finally:
        sock.close()
    return None

def extract_txt_data(dns_response):
    try:
        header = struct.unpack('!HHHHHH', dns_response[:12])
        questions = header[2]
        answers = header[3]
        
        if answers == 0:
            return None
        
        offset = 12
        
        for _ in range(questions):
            while offset < len(dns_response) and dns_response[offset] != 0:
                length = dns_response[offset]
                if length & 0xC0:
                    offset += 2
                    break
                else:
                    offset += 1 + length
            
            if offset < len(dns_response) and dns_response[offset] == 0:
                offset += 1
            offset += 4
        
        for _ in range(answers):
            if offset < len(dns_response) and dns_response[offset] & 0xC0:
                offset += 2
            else:
                while offset < len(dns_response) and dns_response[offset] != 0:
                    length = dns_response[offset]
                    offset += 1 + length
                offset += 1
            
            if offset + 10 > len(dns_response):
                break
            
            rr_type, rr_class, ttl, data_length = struct.unpack('!HHIH', dns_response[offset:offset+10])
            offset += 10
            
            if rr_type == 16:
                if offset + data_length <= len(dns_response):
                    txt_length = dns_response[offset]
                    if txt_length + 1 <= data_length:
                        txt_data = dns_response[offset+1:offset+1+txt_length].decode('utf-8')
                        return txt_data
            
            offset += data_length
    except:
        pass
    return None

def get_file_info(filename, server_ip, domain):
    query_name = f"info.{filename}.{domain}"
    
    for attempt in range(MAX_RETRIES):
        try:
            response = send_dns_query(query_name, 16, server_ip)
            if response:
                txt_data = extract_txt_data(response)
                if txt_data and ':' in txt_data:
                    parts = txt_data.split(':')
                    if len(parts) == 2:
                        total_chunks = int(parts[0])
                        md5_hash = parts[1]
                        return total_chunks, md5_hash
        except Exception as e:
            print(f"Tentativa {attempt + 1} esuata: {e}")
            if attempt < MAX_RETRIES - 1:
                time.sleep(1)
    return None

def download_chunk_with_retry(filename, chunk_id, server_ip, domain):
    query_name = f"{chunk_id}.{filename}.{domain}"
    
    for attempt in range(MAX_RETRIES):
        try:
            response = send_dns_query(query_name, 16, server_ip)
            if response:
                chunk_data = extract_txt_data(response)
                if chunk_data:
                    return chunk_data
        except:
            print(f"(tentativa {attempt + 1} esuata)", end='')
            if attempt < MAX_RETRIES - 1:
                time.sleep(1)
    return None

def save_state(path, state):
    try:
        with open(path, 'w') as f:
            json.dump(state, f)
    except:
        pass

def download_file(filename, server_ip, domain):
    print(f"Incep descarcarea fisierului: {filename}")

    file_info = get_file_info(filename, server_ip, domain)
    if not file_info:
        print(f"Eroare: Nu s-au putut obtine informatii despre fisierul {filename}")
        return False
    total_chunks, expected_md5 = file_info
    print(f"Meta: {total_chunks} chunks, MD5 {expected_md5}")

    chunk_dir = os.path.join(DOWNLOAD_DIR, filename + CHUNK_DIR_SUFFIX)
    state_path = os.path.join(DOWNLOAD_DIR, filename + STATE_SUFFIX)
    final_path = os.path.join(DOWNLOAD_DIR, filename)

    if os.path.isfile(final_path):
        with open(final_path, 'rb') as f:
            existing_md5 = hashlib.md5(f.read()).hexdigest()
        if existing_md5 == expected_md5:
            print("Fisier deja prezent cu MD5 corect. Skip descarcare.")
            return True
        else:
            print("Fisier existent corupt / MD5 diferit. Va fi re-descarcat.")
            os.rename(final_path, final_path + '.bak')

    os.makedirs(chunk_dir, exist_ok=True)

    state = {
        'filename': filename,
        'total_chunks': total_chunks,
        'md5': expected_md5,
        'downloaded': []
    }
    if os.path.isfile(state_path):
        try:
            with open(state_path, 'r') as f:
                prev_state = json.load(f)
            if (prev_state.get('total_chunks') == total_chunks and
                    prev_state.get('md5') == expected_md5):
                state = prev_state
                print(f"Reluare transfer: {len(state['downloaded'])}/{total_chunks} chunks deja descarcate.")
            else:
                print("State vechi incompatibil. Reset.")
        except:
            print("Nu pot citi state vechi. Reset.")

    downloaded_set = set(state['downloaded'])

    for chunk_id in range(total_chunks):
        if chunk_id in downloaded_set and os.path.isfile(os.path.join(chunk_dir, str(chunk_id))):
            continue

        print(f"Chunk {chunk_id + 1}/{total_chunks}...", end=' ')
        chunk_data = download_chunk_with_retry(filename, chunk_id, server_ip, domain)
        if chunk_data is None:
            print("ESUAT")
            print("Transfer intrerupt. Puteti rula din nou pentru reluare.")
            save_state(state_path, state)
            return False
        try:
            with open(os.path.join(chunk_dir, str(chunk_id)), 'w') as cf:
                cf.write(chunk_data)
        except Exception as e:
            print(f"Eroare la salvarea chunk-ului: {e}")
            save_state(state_path, state)
            return False
        state['downloaded'].append(chunk_id)
        downloaded_set.add(chunk_id)
        save_state(state_path, state)
        print("OK")

    if len(downloaded_set) == total_chunks:
        print("Reconstitui fisierul final...")
        try:
            encoded_parts = []
            for cid in range(total_chunks):
                with open(os.path.join(chunk_dir, str(cid)), 'r') as cf:
                    encoded_parts.append(cf.read())
            encoded_data = ''.join(encoded_parts)
            file_data = base64.b64decode(encoded_data)
            actual_md5 = hashlib.md5(file_data).hexdigest()
            if actual_md5 != expected_md5:
                print("Eroare: MD5 incorect dupa reconstituire.")
                print(f"Asteptat: {expected_md5}\nPrimit:   {actual_md5}")
                return False
            with open(final_path, 'wb') as f:
                f.write(file_data)
            for cid in range(total_chunks):
                try:
                    os.remove(os.path.join(chunk_dir, str(cid)))
                except OSError:
                    pass
            try:
                os.rmdir(chunk_dir)
            except OSError:
                pass
            try:
                os.remove(state_path)
            except OSError:
                pass
            print(f"Fisier salvat: {final_path} ({len(file_data)} bytes) MD5 {actual_md5}")
            return True
        except Exception as e:
            print(f"Eroare la reconstituire: {e}")
            return False
    else:
        print("Nu toate chunk-urile au fost descarcate. Reluati mai tarziu.")
        return False

if len(sys.argv) < 3:
    print("Utilizare: python3 dns_client.py <server_ip> <filename> [domain]")
    print("Exemplu: python3 dns_client.py 192.168.1.100 test.txt tunel.live")
    sys.exit(1)

server_ip = sys.argv[1]
filename = sys.argv[2]
domain = sys.argv[3] if len(sys.argv) > 3 else "tunel.live"

print("=== DNS Tunnel Client ===")
print(f"Server: {server_ip}")
print(f"Fisier: {filename}")
print(f"Domeniu: {domain}")
print()

try:
    success = download_file(filename, server_ip, domain)
    if success:
        print("\nDescarcare reusita!")
    else:
        print("\nDescarcare esuata!")
        sys.exit(1)
except KeyboardInterrupt:
    print("\nDescarcare intrerupta de utilizator.")
except Exception as e:
    print(f"\nEroare: {e}")
    sys.exit(1)
