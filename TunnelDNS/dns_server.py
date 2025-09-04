#!/usr/bin/env python3
import socket
import struct
import hashlib
import os
import base64

# Configuration
DOMAIN = "t.mytini.live"
FILES_DIR = "./server_files"
CHUNK_SIZE = 200

# File sessions cache
sessions = {}

# Create files directory
os.makedirs(FILES_DIR, exist_ok=True)

def encode_dns_name(name):
    encoded = b''
    for part in name.split('.'):
        if part:
            encoded += struct.pack('!B', len(part)) + part.encode('utf-8')
    encoded += b'\x00'
    return encoded

def create_txt_response(transaction_id, query_name, txt_data):
    flags = 0x8000
    header = struct.pack('!HHHHHH', transaction_id, flags, 1, 1, 0, 0)
    question = encode_dns_name(query_name) + struct.pack('!HH', 16, 1)
    answer_name = encode_dns_name(query_name)
    txt_bytes = txt_data.encode('utf-8')
    txt_record = struct.pack('!B', len(txt_bytes)) + txt_bytes
    answer = answer_name + struct.pack('!HHIH', 16, 1, 600, len(txt_record)) + txt_record
    return header + question + answer

def create_nxdomain_response(transaction_id, query_name, query_type):
    flags = 0x8003
    header = struct.pack('!HHHHHH', transaction_id, flags, 1, 0, 0, 0)
    question = encode_dns_name(query_name) + struct.pack('!HH', query_type, 1)
    return header + question

def parse_dns_question(data):
    name_parts = []
    offset = 0
    while offset < len(data):
        length = data[offset]
        if length == 0:
            offset += 1
            break
        if length & 0xC0:
            break
        name_parts.append(data[offset+1:offset+1+length].decode('utf-8'))
        offset += 1 + length
    
    name = '.'.join(name_parts)
    if offset + 4 <= len(data):
        query_type, query_class = struct.unpack('!HH', data[offset:offset+4])
    else:
        query_type = query_class = 0
    return name, query_type, query_class

def get_file_session(file_path, addr):
    session_key = f"{addr[0]}:{os.path.basename(file_path)}"
    if session_key not in sessions:
        with open(file_path, 'rb') as f:
            file_data = f.read()
        md5_hash = hashlib.md5(file_data).hexdigest()
        encoded_data = base64.b64encode(file_data).decode('ascii')
        chunks = [encoded_data[i:i+CHUNK_SIZE] for i in range(0, len(encoded_data), CHUNK_SIZE)]
        sessions[session_key] = {'chunks': chunks, 'total_chunks': len(chunks), 'md5': md5_hash}
    return sessions[session_key]

# DNS server
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind(("0.0.0.0", 53))
print("DNS tunnel server started on 0.0.0.0:53")

while True:
    try:
        data, addr = sock.recvfrom(512)
        
        # Parse DNS request
        header = struct.unpack('!HHHHHH', data[:12])
        transaction_id = header[0]
        questions = header[2]
        
        if questions == 0:
            continue
            
        query_name, query_type, query_class = parse_dns_question(data[12:])
        
        # Check if query is for our domain
        if not query_name.endswith(DOMAIN):
            response = create_nxdomain_response(transaction_id, query_name, query_type)
            sock.sendto(response, addr)
            continue
            
        # Only handle TXT records
        if query_type != 16:
            response = create_nxdomain_response(transaction_id, query_name, query_type)
            sock.sendto(response, addr)
            continue
            
        # Parse tunnel request: chunk_id.filename.domain
        parts = query_name.split('.')
        if len(parts) < 3:
            response = create_nxdomain_response(transaction_id, query_name, query_type)
            sock.sendto(response, addr)
            continue
            
        chunk_id = parts[0]
        filename = parts[1]
        file_path = os.path.join(FILES_DIR, filename)
        
        if not os.path.exists(file_path):
            response = create_nxdomain_response(transaction_id, query_name, query_type)
            sock.sendto(response, addr)
            continue
            
        session = get_file_session(file_path, addr)
        
        if chunk_id == "info":
            info = f"{session['total_chunks']}:{session['md5']}"
            response = create_txt_response(transaction_id, query_name, info)
        else:
            try:
                chunk_num = int(chunk_id)
                if 0 <= chunk_num < len(session['chunks']):
                    chunk_data = session['chunks'][chunk_num]
                    response = create_txt_response(transaction_id, query_name, chunk_data)
                else:
                    response = create_nxdomain_response(transaction_id, query_name, query_type)
            except ValueError:
                response = create_nxdomain_response(transaction_id, query_name, query_type)
                
        sock.sendto(response, addr)
        
    except Exception as e:
        print(f"Error: {e}")
        continue