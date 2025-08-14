import socket
import requests

# read blocked domains from log
f = open("data/blocked_domains.log")
lines = f.readlines()
f.close()

domains = []
for line in lines:
    line = line.strip()
    if line:
        if ' - ' in line:
            domain = line.split(' - ')[-1]
        else:
            domain = line
        domains.append(domain.lower())

# count domains
domain_count = {}
for domain in domains:
    if domain in domain_count:
        domain_count[domain] += 1
    else:
        domain_count[domain] = 1

# write stats
out = open("data/domain_stats.txt", "w")

# top 5 domains
out.write("Top 5 domenii:\n")
sorted_domains = sorted(domain_count.items(), key=lambda x: x[1], reverse=True)
for i in range(min(5, len(sorted_domains))):
    domain, count = sorted_domains[i]
    out.write(domain + ": " + str(count) + "\n")

# company stats
companies = ['google', 'facebook', 'doubleclick', 'linkedin', 'amazon', 'yahoo']
out.write("\nStatistici companii:\n")
for company in companies:
    total = 0
    for domain in domain_count:
        if company in domain:
            total += domain_count[domain]
    out.write(company + ": " + str(total) + " blocări\n")

# domain details
out.write("\nDomeniu\t\t\t\t\tIP\t\t\tORG\n")
out.write("-" * 80 + "\n")

unique_domains = list(set(domains))
for domain in unique_domains:
    try:
        ip = socket.gethostbyname(domain)
        # get org info
        resp = requests.get("https://ipinfo.io/" + ip + "/json?token=5cc1c304437a11")
        data = resp.json()
        org = data.get('org', 'Unknown')
        out.write(domain.ljust(40) + " " + ip.ljust(15) + " " + org + "\n")
    except:
        out.write(domain.ljust(40) + " lookup failed\n")

out.close()
print("stats written")
