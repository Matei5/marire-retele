#!/bin/bash
set -x
# remove default gateway 198.10.1.1
ip route del default
# make router container the default router
ip route add default via 172.29.0.254
# add 8.8.8.8 nameserver
echo "nameserver 8.8.8.8" >> /etc/resolv.conf
# we need to drop the kernel reset of hand-coded tcp connections
# https://stackoverflow.com/a/8578541
iptables -A OUTPUT -p tcp --tcp-flags RST RST -j DROP

