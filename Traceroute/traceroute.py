import socket
import requests
import time
import json
import os
import subprocess
import re

def traceroute(target, max_hops=10):
    # Get the IP address
    dest_ip = socket.gethostbyname(target)
    print(f"Traceroute to {target} ({dest_ip})")
    
    # Use system tracert command (more reliable on Windows)
    cmd = f"tracert -h {max_hops} {target}"
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    
    hops = []
    lines = result.stdout.split('\n')
    
    for line in lines:
        # Parse tracert output format: "  1    <1 ms    <1 ms    <1 ms  192.168.1.1"
        match = re.search(r'^\s*(\d+)\s+(.+)', line)
        if match:
            hop_num = int(match.group(1)) 
            rest = match.group(2).strip()
            
            # Extract IP address (last token that looks like an IP)
            tokens = rest.split()
            hop_ip = None
            
            for token in reversed(tokens):
                # Check if token looks like an IP address
                if re.match(r'\d+\.\d+\.\d+\.\d+', token):
                    hop_ip = token
                    break
            
            # Extract timing info
            rtt_ms = None
            # Find all timing patterns in the line
            timing_matches = re.findall(r'(<?\d+)\s*ms|(\*)\s*ms', rest)
            if timing_matches:
                # Take the first valid timing
                for match in timing_matches:
                    if match[0]:  # First group (number)
                        try:
                            # Remove '<' if present and convert to int
                            time_str = match[0].replace('<', '')
                            rtt_ms = int(time_str)
                            break
                        except:
                            pass
            
            # Get location info
            city = region = country = ""
            if hop_ip:
                response = requests.get(f"http://ip-api.com/json/{hop_ip}")
                if response.status_code == 200:
                    data = response.json()
                    if data.get("status") == "success":
                        city = data.get("city", "")
                        region = data.get("regionName", "")
                        country = data.get("country", "")
                time.sleep(1)  # Don't spam the API
            
            hops.append({
                "hop": hop_num,
                "ip": hop_ip,
                "rtt_ms": rtt_ms,
                "city": city,
                "region": region,
                "country": country
            })
            
            print(f"{hop_num:2d}  {hop_ip or '*':15}  {rtt_ms or '*':>6} ms  {city} {region} {country}")
    
    return {"target": target, "target_ip": dest_ip, "hops": hops}

# Just run the traceroute and save results
targets = ['google.com']  # Test with google
reports = []

for target in targets:
    print(f"Tracing route to {target}...")
    report = traceroute(target)
    reports.append(report)

# Save the results
os.makedirs("routes", exist_ok=True)

# Save JSON files
for report in reports:
    filename = f"routes/{report['target'].replace('/', '_')}_{report['target_ip']}.json"
    with open(filename, 'w') as f:
        json.dump(report, f, indent=2)

# Make a simple markdown report
md_content = "# Traceroute Report\n\n"
for report in reports:
    md_content += f"## {report['target']} ({report['target_ip']})\n\n"
    md_content += "| Hop | IP Address | RTT (ms) | City | Region | Country |\n"
    md_content += "|-----|------------|----------|------|--------|---------|\n"
    
    for hop in report['hops']:
        ip = hop['ip'] or '*'
        rtt = hop['rtt_ms'] if hop['rtt_ms'] is not None else '*'
        md_content += f"| {hop['hop']} | {ip} | {rtt} | {hop['city']} | {hop['region']} | {hop['country']} |\n"
    
    md_content += "\n"

with open("routes/traceroute_report.md", 'w') as f:
    f.write(md_content)

print("Saved reports to routes/ directory")

