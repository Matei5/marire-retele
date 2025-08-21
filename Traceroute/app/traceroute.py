import socket
import traceback
import requests
import time
import argparse
import json
import os
import ipaddress
import sys
import argparse
import json
import os
import time

# socket de UDP
udp_send_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, proto=socket.IPPROTO_UDP)

# socket RAW de citire a răspunsurilor ICMP
icmp_recv_socket = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_ICMP)
# setam timout in cazul in care socketul ICMP la apelul recvfrom nu primeste nimic in buffer
icmp_recv_socket.settimeout(3)

def traceroute(ip, port):
    # setam TTL in headerul de IP pentru socketul de UDP
    TTL = 64
    udp_send_sock.setsockopt(socket.IPPROTO_IP, socket.IP_TTL, TTL)

    # trimite un mesaj UDP catre un tuplu (IP, port)
    udp_send_sock.sendto(b'salut', (ip, port))

    # asteapta un mesaj ICMP de tipul ICMP TTL exceeded messages
    # in cazul nostru nu verificăm tipul de mesaj ICMP
    # puteti verifica daca primul byte are valoarea Type == 11
    # https://tools.ietf.org/html/rfc792#page-5
    # https://en.wikipedia.org/wiki/Internet_Control_Message_Protocol#Header
    addr = 'done!'
    try:
        data, addr = icmp_recv_socket.recvfrom(63535)
    except Exception as e:
        print("Socket timeout ", str(e))
        print(traceback.format_exc())
    print (addr)
    return addr


def geo_ip(ip):
    """Query ip-api.com for IP geolocation. Returns dict with city, regionName, country, lat, lon."""
    if is_private_ip(ip):
        return {"status": "private", "query": ip}
    
    try:
        response = requests.get(f"http://ip-api.com/json/{ip}?fields=status,city,regionName,country,lat,lon,query,message", timeout=5)
        return response.json()
    except Exception as e:
        return {"status": "fail", "message": str(e), "query": ip}


def is_private_ip(ip):
    """Check if IP is private/local."""
    try:
        return ipaddress.ip_address(ip).is_private
    except Exception:
        return False


def full_traceroute(target, port=33434, max_hops=30, timeout=3):
    """Complete UDP traceroute implementation with geolocation."""
    try:
        dest_ip = socket.gethostbyname(target)
    except Exception as e:
        print(f"Cannot resolve {target}: {e}")
        return None

    print(f"Traceroute to {target} ({dest_ip}), max {max_hops} hops")
    
    # Create ICMP socket for receiving replies
    try:
        icmp_sock = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_ICMP)
        icmp_sock.settimeout(timeout)
    except PermissionError:
        print("ERROR: Raw sockets require root privileges. Run with sudo.")
        return None

    route = []
    
    for ttl in range(1, max_hops + 1):
        # Create UDP socket for sending
        udp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        udp_sock.setsockopt(socket.SOL_IP, socket.IP_TTL, ttl)
        
        hop_ip = None
        rtt_ms = None
        
        try:
            start_time = time.time()
            udp_sock.sendto(b'traceroute', (dest_ip, port))
            
            try:
                data, addr = icmp_sock.recvfrom(65535)
                end_time = time.time()
                rtt_ms = int((end_time - start_time) * 1000)
                hop_ip = addr[0]
            except socket.timeout:
                pass
        except Exception:
            pass
        finally:
            udp_sock.close()
        
        # Get geolocation for this hop
        geo_info = None
        if hop_ip:
            geo_info = geo_ip(hop_ip)
            time.sleep(0.1)  # Rate limiting for ip-api
        
        route.append({
            "hop": ttl,
            "ip": hop_ip,
            "rtt_ms": rtt_ms,
            "geo": geo_info
        })
        
        # Print hop info
        geo_str = ""
        if geo_info and geo_info.get("status") == "success":
            city = geo_info.get("city", "")
            region = geo_info.get("regionName", "")
            country = geo_info.get("country", "")
            geo_str = f" {city} {region} {country}".strip()
        elif geo_info and geo_info.get("status") == "private":
            geo_str = " (private)"
        
        print(f"{ttl:2d}  {hop_ip or '*':15}  {rtt_ms or '*'} ms{geo_str}")
        
        # Check if we reached destination
        if hop_ip == dest_ip:
            break
    
    icmp_sock.close()
    return {
        "target": target,
        "target_ip": dest_ip,
        "route": route
    }


def save_md_report(reports, out_dir='routes'):
    """Save individual JSON files and combined Markdown report."""
    os.makedirs(out_dir, exist_ok=True)
    
    # Save individual JSON files
    for report in reports:
        if not report:
            continue
        filename = f"{report['target'].replace('/', '_')}_{report['target_ip']}.json"
        json_path = os.path.join(out_dir, filename)
        with open(json_path, 'w') as f:
            json.dump(report, f, indent=2)
    
    # Create combined Markdown report
    md_lines = ["# Traceroute Report", ""]
    md_lines.append("Analysis of network routes to sites in Asia (.cn), Africa (.za), and Australia (.au)")
    md_lines.append("")
    
    for report in reports:
        if not report:
            continue
        
        md_lines.append(f"## {report['target']} ({report['target_ip']})")
        md_lines.append("")
        md_lines.append("| Hop | IP Address | RTT (ms) | City | Region | Country |")
        md_lines.append("|-----|------------|----------|------|--------|---------|")
        
        for hop in report['route']:
            ip = hop['ip'] or '*'
            rtt = hop['rtt_ms'] if hop['rtt_ms'] is not None else '*'
            city = region = country = ''
            
            if hop['geo'] and hop['geo'].get('status') == 'success':
                city = hop['geo'].get('city', '')
                region = hop['geo'].get('regionName', '')
                country = hop['geo'].get('country', '')
            elif hop['geo'] and hop['geo'].get('status') == 'private':
                city = 'Private IP'
            
            md_lines.append(f"| {hop['hop']} | {ip} | {rtt} | {city} | {region} | {country} |")
        
        md_lines.append("")
    
    # Save combined report
    md_path = os.path.join(out_dir, 'combined_report.md')
    with open(md_path, 'w') as f:
        f.write('\n'.join(md_lines))
    
    print(f"Saved combined Markdown report to {md_path}")
    return md_path

'''
 Exercitiu hackney carriage (optional)!
    e posibil ca ipinfo sa raspunda cu status code 429 Too Many Requests
    cititi despre campul X-Forwarded-For din antetul HTTP
        https://www.nginx.com/resources/wiki/start/topics/examples/forwarded/
    si setati-l o valoare in asa fel incat
    sa puteti trece peste sistemul care limiteaza numarul de cereri/zi

    Alternativ, puteti folosi ip-api (documentatie: https://ip-api.com/docs/api:json).
    Acesta permite trimiterea a 45 de query-uri de geolocare pe minut.
'''

# exemplu de request la IP info pentru a
# obtine informatii despre localizarea unui IP
fake_HTTP_header = {
                    'referer': 'https://ipinfo.io/',
                    'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/67.0.3396.79 Safari/537.36'
                   }


def geo_ip(ip):
    """Use ip-api.com to get basic geolocation for an IP. Returns dict or None."""
    try:
        r = requests.get(f"http://ip-api.com/json/{ip}?fields=status,city,regionName,country,query,message", timeout=5)
        return r.json()
    except Exception:
        return {"status": "fail", "message": "request_error", "query": ip}


def is_private_ip(ip):
    return ip.startswith('10.') or ip.startswith('192.168.') or ip.startswith('172.')


def save_md_report(reports, out_dir='routes'):
    os.makedirs(out_dir, exist_ok=True)
    md_lines = ["# Traceroute reports", ""]
    for rep in reports:
        md_lines.append(f"## {rep['target']} ({rep['target_ip']})")
        md_lines.append("")
        md_lines.append("| Hop | IP | RTT (ms) | City | Region | Country |")
        md_lines.append("|---:|:---:|:---:|:---|:---|:---:|")
        for h in rep['hops']:
            ip = h.get('ip') or '*'
            rtt = h.get('rtt') if h.get('rtt') is not None else '*'
            city = h.get('city', '')
            region = h.get('region', '')
            country = h.get('country', '')
            md_lines.append(f"| {h['hop']} | {ip} | {rtt} | {city} | {region} | {country} |")
        md_lines.append("")
    with open(os.path.join(out_dir, 'combined_report.md'), 'w') as f:
        f.write('\n'.join(md_lines))
    print(f"Saved combined Markdown report to {out_dir}/combined_report.md")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Minimal traceroute runner')
    parser.add_argument('targets', nargs='*', help='target hostnames or IPs (defaults to sina.cn, google.co.za, abc.net.au)')
    parser.add_argument('--max-hops', type=int, default=30)
    parser.add_argument('--port', type=int, default=33434)
    parser.add_argument('--timeout', type=int, default=3)
    args = parser.parse_args()

    targets = args.targets or ['sina.cn', 'google.co.za', 'abc.net.au']
    icmp_recv_socket.settimeout(args.timeout)

    all_reports = []
    for t in targets:
        try:
            dest = socket.gethostbyname(t)
        except Exception as e:
            print(f"Cannot resolve {t}: {e}")
            continue
        print(f"\nTracing to {t} ({dest})")
        hops = []
        for ttl in range(1, args.max_hops + 1):
            # set TTL for UDP socket and send
            udp_send_sock.setsockopt(socket.IPPROTO_IP, socket.IP_TTL, ttl)
            try:
                start = time.time()
                udp_send_sock.sendto(b'salut', (dest, args.port))
                try:
                    data, addr = icmp_recv_socket.recvfrom(63535)
                    rtt = int((time.time() - start) * 1000)
                    hop_ip = addr[0]
                except socket.timeout:
                    hop_ip = None
                    rtt = None
            except Exception as e:
                print(f"Send error at ttl {ttl}: {e}")
                hop_ip = None
                rtt = None

            city = region = country = ''
            if hop_ip and not is_private_ip(hop_ip):
                geo = geo_ip(hop_ip)
                if isinstance(geo, dict) and geo.get('status') == 'success':
                    city = geo.get('city','')
                    region = geo.get('regionName','')
                    country = geo.get('country','')
            elif hop_ip and is_private_ip(hop_ip):
                city = 'private'

            print(f"{ttl:2d}  {hop_ip or '*':15}  {rtt if rtt is not None else '*'} ms   {city} {region} {country}")
            hops.append({'hop': ttl, 'ip': hop_ip, 'rtt': rtt, 'city': city, 'region': region, 'country': country})

            if hop_ip == dest:
                break

        all_reports.append({'target': t, 'target_ip': dest, 'hops': hops})

    save_md_report(all_reports)

    # Example of IP info calls (moved here so they don't run on import). Wrapped in try/except.
    try:
        raspuns = requests.get('https://ipinfo.io/widget/193.226.51.6', headers=fake_HTTP_header, timeout=5)
        try:
            print('\nExample ipinfo result for 193.226.51.6:')
            print(raspuns.json())
        except ValueError:
            print('ipinfo example request failed: invalid JSON, status:', raspuns.status_code, 'body:', raspuns.text[:200])
    except requests.RequestException as e:
        print('ipinfo example request failed:', e)

    try:
        raspuns = requests.get('https://ipinfo.io/widget/10.0.0.1', headers=fake_HTTP_header, timeout=5)
        try:
            print('\nExample ipinfo result for 10.0.0.1:')
            print(raspuns.json())
        except ValueError:
            print('ipinfo example request failed: invalid JSON, status:', raspuns.status_code, 'body:', raspuns.text[:200])
    except requests.RequestException as e:
        print('ipinfo example request failed:', e)

