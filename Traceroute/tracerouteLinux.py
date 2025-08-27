import socket
import requests
import time
import json
import os
import subprocess
import re

def traceroute(target, max_hops=30):
    # Get the IP address
    dest_ip = socket.gethostbyname(target)
    
    # Get source IP
    temp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    temp_sock.connect(("8.8.8.8", 80))  # Finding my external IP
    source_ip = temp_sock.getsockname()[0]
    temp_sock.close()
    
    print(f"Traceroute from {source_ip} to {target} ({dest_ip})")
    
    result = subprocess.run(f"traceroute -m {max_hops} -n {target}", shell=True, capture_output=True, text=True)
    
    hops = []
    lines = result.stdout.split('\n')
    
    for line in lines:
        # Parse traceroute output format: " 1  192.168.1.1  1.234 ms  1.567 ms  1.890 ms"
        match = re.search(r'^\s*(\d+)\s+(.+)', line)
        if match:
            hop_num = int(match.group(1)) 
            rest = match.group(2).strip()
            
            # Skip lines with just asterisks
            if rest == '* * *' or not rest:
                hops.append({
                    "hop": hop_num,
                    "ip": None,
                    "rtt_ms": None,
                    "city": "",
                    "region": "",
                    "country": "",
                    "geo": None
                })
                print(f"{hop_num:2d}  {'*':15}  {'*':>6} ms")
                continue
            
            # Extract IP address
            tokens = rest.split()
            hop_ip = None
            
            for token in tokens:
                # Check if token looks like an IP address
                if re.match(r'\d+\.\d+\.\d+\.\d+', token):
                    hop_ip = token
                    break
            
            # Extract timing info
            rtt_ms = None
            timing_matches = re.findall(r'(\d+\.?\d*)\s*ms', rest)
            if timing_matches:
                try:
                    rtt_ms = float(timing_matches[0])
                except:
                    pass
            
            # Get location info
            city = region = country = ""
            lat = lon = None
            if hop_ip and not is_private_ip(hop_ip):
                try:
                    response = requests.get(f"http://ip-api.com/json/{hop_ip}?fields=status,city,regionName,country,lat,lon", timeout=5)
                    if response.status_code == 200:
                        data = response.json()
                        if data.get("status") == "success":
                            city = data.get("city", "")
                            region = data.get("regionName", "")
                            country = data.get("country", "")
                            lat = data.get("lat")
                            lon = data.get("lon")
                    time.sleep(0.5)  # Rate limit for ip-api
                except Exception as e:
                    print(f"  Warning: Could not get location for {hop_ip}: {e}")
            elif hop_ip and is_private_ip(hop_ip):
                city = "private"
            
            hops.append({
                "hop": hop_num,
                "ip": hop_ip,
                "rtt_ms": rtt_ms,
                "city": city,
                "region": region,
                "country": country,
                "geo": {
                    "status": "success" if lat is not None else "fail",
                    "lat": lat,
                    "lon": lon,
                    "city": city,
                    "country": country
                } if lat is not None else None
            })
            
            print(f"{hop_num:2d}  {hop_ip or '*':15}  {rtt_ms or '*':>6} ms  {city} {region} {country}")
    
    return {"target": target, "target_ip": dest_ip, "source_ip": source_ip, "hops": hops}

def is_private_ip(ip):
    octets = [int(x) for x in ip.split('.')]
    # 10.0.0.0/8, 172.16.0.0/12, 192.168.0.0/16
    return (octets[0] == 10 or 
            (octets[0] == 172 and 16 <= octets[1] <= 31) or
            (octets[0] == 192 and octets[1] == 168) or
            octets[0] == 127)  # localhost

# Test sites
targets = [
    'sina.cn',      # Asia - China
    'baidu.com',    # Asia - China
    'google.co.za', # Africa - South Africa
    'news24.com',   # Africa - South Africa  
    'abc.net.au',   # Australia
    'news.com.au'   # Australia
]
reports = []

for target in targets:
    print(f"Tracing route to {target}...")
    report = traceroute(target)
    reports.append(report)

# Save the results
os.makedirs("routes", exist_ok=True)

# JSON files
for report in reports:
    filename = f"routes/{report['source_ip']}_{report['target'].replace('/', '_')}_{report['target_ip']}.json"
    with open(filename, 'w') as f:
        json.dump(report, f, indent=2)

# Markdown report
# Prepare markdown content for this run
run_content = ""

# Get source IP from first report
source_ip = reports[0]['source_ip'] if reports else "unknown"
run_content += f"## Run from {source_ip}\n\n"

for report in reports:
    run_content += f"### {report['target']} ({report['target_ip']})\n\n"
    run_content += "| Hop | IP Address | RTT (ms) | City | Region | Country |\n"
    run_content += "|-----|------------|----------|------|--------|---------|\n"
    
    for hop in report['hops']:
        ip = hop['ip'] or '*'
        rtt = hop['rtt_ms'] if hop['rtt_ms'] is not None else '*'
        run_content += f"| {hop['hop']} | {ip} | {rtt} | {hop['city']} | {hop['region']} | {hop['country']} |\n"
    
    run_content += "\n"

run_content += "\n---\n\n"

print("Saved JSON reports to routes/ directory")

add_to_report = input("Add this run to the markdown report? (y/n): ").lower().strip()

if add_to_report in ['y', 'yes']:
    report_file = "routes/traceroute_report.md"
    
    # Check if file exists, if not create header
    if not os.path.exists(report_file):
        with open(report_file, 'w') as f:
            f.write("# Traceroute Report\n\n")

    # Append
    with open(report_file, 'a') as f:
        f.write(run_content)
    
    print(f"Added run to {report_file}")
else:
    print("Skipped adding to markdown report")

