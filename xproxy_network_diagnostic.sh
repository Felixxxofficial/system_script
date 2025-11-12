#!/bin/bash

# XProxy Network Diagnostic Script
# This script diagnoses network connectivity and DNS issues affecting xproxy

echo "========================================="
echo "XProxy Network Diagnostic Tool"
echo "========================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    local status=$1
    local message=$2
    case $status in
        "OK")
            echo -e "${GREEN}[✓]${NC} $message"
            ;;
        "FAIL")
            echo -e "${RED}[✗]${NC} $message"
            ;;
        "WARN")
            echo -e "${YELLOW}[!]${NC} $message"
            ;;
        "INFO")
            echo -e "${BLUE}[i]${NC} $message"
            ;;
    esac
}

# 1. Check network interfaces
echo "1. Network Interface Analysis:"
echo "------------------------------"
interfaces=$(ip link show | grep -E '^[0-9]+:' | awk -F': ' '{print $2}' | grep -v lo)
for iface in $interfaces; do
    if ip addr show $iface | grep -q "inet "; then
        ip_addr=$(ip addr show $iface | grep "inet " | awk '{print $2}' | head -1)
        print_status "OK" "Interface $iface: $ip_addr"
    else
        print_status "WARN" "Interface $iface: No IP address"
    fi
done
echo ""

# 2. Check routing table
echo "2. Routing Table Analysis:"
echo "--------------------------"
default_routes=$(ip route show | grep "^default")
route_count=$(echo "$default_routes" | wc -l)

if [ $route_count -gt 1 ]; then
    print_status "WARN" "Multiple default routes detected ($route_count):"
    echo "$default_routes" | while read route; do
        echo "   $route"
    done
else
    print_status "OK" "Single default route:"
    echo "   $default_routes"
fi
echo ""

# 3. Test basic connectivity
echo "3. Connectivity Tests:"
echo "----------------------"
# Test ping to Google DNS
if ping -c 3 -W 5 8.8.8.8 >/dev/null 2>&1; then
    print_status "OK" "Can ping 8.8.8.8 (Google DNS)"
else
    print_status "FAIL" "Cannot ping 8.8.8.8"
fi

# Test ping to Cloudflare DNS
if ping -c 3 -W 5 1.1.1.1 >/dev/null 2>&1; then
    print_status "OK" "Can ping 1.1.1.1 (Cloudflare DNS)"
else
    print_status "FAIL" "Cannot ping 1.1.1.1"
fi
echo ""

# 4. DNS Resolution Tests
echo "4. DNS Resolution Tests:"
echo "------------------------"
# Check resolv.conf
if [ -f /etc/resolv.conf ]; then
    print_status "INFO" "DNS servers in /etc/resolv.conf:"
    grep "^nameserver" /etc/resolv.conf | while read line; do
        echo "   $line"
    done
else
    print_status "FAIL" "/etc/resolv.conf not found"
fi

# Test DNS resolution with different methods
echo ""
print_status "INFO" "Testing DNS resolution methods:"

# Test with nslookup
if command -v nslookup >/dev/null 2>&1; then
    if timeout 10 nslookup google.com >/dev/null 2>&1; then
        print_status "OK" "nslookup google.com works"
    else
        print_status "FAIL" "nslookup google.com fails"
    fi
else
    print_status "WARN" "nslookup not available"
fi

# Test with dig
if command -v dig >/dev/null 2>&1; then
    if timeout 10 dig @8.8.8.8 google.com >/dev/null 2>&1; then
        print_status "OK" "dig @8.8.8.8 google.com works"
    else
        print_status "FAIL" "dig @8.8.8.8 google.com fails"
    fi
    
    if timeout 10 dig @1.1.1.1 google.com >/dev/null 2>&1; then
        print_status "OK" "dig @1.1.1.1 google.com works"
    else
        print_status "FAIL" "dig @1.1.1.1 google.com fails"
    fi
else
    print_status "WARN" "dig not available"
fi

# Test with host
if command -v host >/dev/null 2>&1; then
    if timeout 10 host google.com >/dev/null 2>&1; then
        print_status "OK" "host google.com works"
    else
        print_status "FAIL" "host google.com fails"
    fi
else
    print_status "WARN" "host not available"
fi
echo ""

# 5. Check xproxy status
echo "5. XProxy Status:"
echo "-----------------"
if systemctl is-active --quiet xproxy 2>/dev/null; then
    print_status "OK" "XProxy service is running"
elif pgrep -f xproxy >/dev/null 2>&1; then
    print_status "OK" "XProxy process is running"
else
    print_status "WARN" "XProxy is not running"
fi

# Check xproxy log for recent errors
if [ -f /opt/xproxy/log/xproxy.log ]; then
    recent_errors=$(tail -50 /opt/xproxy/log/xproxy.log | grep -c "connect failed\|timed out\|ERROR")
    if [ $recent_errors -gt 0 ]; then
        print_status "WARN" "Found $recent_errors recent errors in xproxy log"
    else
        print_status "OK" "No recent errors in xproxy log"
    fi
else
    print_status "WARN" "XProxy log file not found"
fi
echo ""

# 6. Interface-specific tests
echo "6. Interface-Specific DNS Tests:"
echo "--------------------------------"
for iface in eth0 enx3acd9372316e enxb2b7a3e9b20b; do
    if ip addr show $iface >/dev/null 2>&1; then
        if timeout 10 dig @8.8.8.8 +tcp +time=5 google.com >/dev/null 2>&1; then
            print_status "OK" "DNS works through $iface"
        else
            print_status "FAIL" "DNS fails through $iface"
        fi
    fi
done
echo ""

# 7. Recommendations
echo "7. Recommendations:"
echo "-------------------"
if [ $route_count -gt 1 ]; then
    print_status "INFO" "Remove extra default routes:"
    echo "   sudo ip route del default via 192.168.107.1 dev enx3acd9372316e"
fi

if ! timeout 10 nslookup google.com >/dev/null 2>&1; then
    print_status "INFO" "Fix DNS resolution:"
    echo "   sudo systemctl restart systemd-resolved"
    echo "   Or manually set DNS: echo 'nameserver 8.8.8.8' | sudo tee /etc/resolv.conf"
fi

print_status "INFO" "To fix xproxy, configure it to use only eth0 interface"
print_status "INFO" "Check xproxy config in /opt/xproxy/ or /etc/xproxy/"

echo ""
echo "========================================="
echo "Diagnostic complete!"
echo "========================================="