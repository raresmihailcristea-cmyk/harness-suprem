#!/bin/bash
# Copyright 2026 Scion Frontiers & Antigravity
# Multi-Provider Security Firewall for Supreme Harness

set -euo pipefail
IFS=$'\n\t'

# 1. Extract Docker DNS info BEFORE any flushing
DOCKER_DNS_RULES=$(iptables-save -t nat 2>/dev/null | grep "127\.0\.0\.11" || true)

# Flush existing rules
iptables -F 2>/dev/null || true
iptables -X 2>/dev/null || true
iptables -t nat -F 2>/dev/null || true
iptables -t nat -X 2>/dev/null || true
iptables -t mangle -F 2>/dev/null || true
iptables -t mangle -X 2>/dev/null || true
ipset destroy allowed-domains 2>/dev/null || true

# 2. Selectively restore ONLY internal Docker DNS resolution
if [ -n "$DOCKER_DNS_RULES" ]; then
    iptables -t nat -N DOCKER_OUTPUT 2>/dev/null || true
    iptables -t nat -N DOCKER_POSTROUTING 2>/dev/null || true
    echo "$DOCKER_DNS_RULES" | xargs -L 1 iptables -t nat 2>/dev/null || true
fi

# Allow DNS and loopback
iptables -A OUTPUT -p udp --dport 53 -j ACCEPT
iptables -A INPUT -p udp --sport 53 -j ACCEPT
iptables -A OUTPUT -p tcp --dport 53 -j ACCEPT
iptables -A INPUT -p tcp --sport 53 -j ACCEPT
iptables -A OUTPUT -p tcp --dport 22 -j ACCEPT
iptables -A INPUT -p tcp --sport 22 -m state --state ESTABLISHED -j ACCEPT
iptables -A INPUT -i lo -j ACCEPT
iptables -A OUTPUT -o lo -j ACCEPT

# Create ipset with CIDR support
ipset create allowed-domains hash:net 2>/dev/null || true

# Add allowed model & provider endpoints
DOMAINS=(
    "api.deepseek.com"
    "api.anthropic.com"
    "api.openai.com"
    "generativelanguage.googleapis.com"
    "api.x.ai"
    "integrate.api.nvidia.com"
    "registry.npmjs.org"
    "pypi.org"
    "files.pythonhosted.org"
)

for domain in "${DOMAINS[@]}"; do
    ips=$(dig +noall +answer A "$domain" 2>/dev/null | awk '$4 == "A" {print $5}' || true)
    for ip in $ips; do
        if [[ "$ip" =~ ^[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}$ ]]; then
            ipset add allowed-domains "$ip" 2>/dev/null || true
        fi
    done
done

# Allow established connections
iptables -A INPUT -m state --state ESTABLISHED,RELATED -j ACCEPT
iptables -A OUTPUT -m state --state ESTABLISHED,RELATED -j ACCEPT

# Allow outbound traffic to allowed domains
iptables -A OUTPUT -m set --match-set allowed-domains dst -j ACCEPT

# Prevent access to Cloud Metadata Services (Anti-SSRF protection)
iptables -A OUTPUT -d 169.254.169.254 -j REJECT --reject-with icmp-admin-prohibited
iptables -A OUTPUT -d 169.254.169.253 -j REJECT --reject-with icmp-admin-prohibited

echo "[supreme-firewall] Security policies and metadata guards initialized."
