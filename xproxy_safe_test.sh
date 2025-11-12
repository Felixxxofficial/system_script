#!/bin/bash

# XProxy Safe Test Script - Shows what would be changed WITHOUT making changes
# This script analyzes your system and shows what the fix scripts would do

echo "========================================="
echo "XProxy Safe Analysis Tool"
echo "This script ONLY analyzes - NO CHANGES"
echo "========================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_status() {
    local status=$1
    local message=$2
    case $status in
        "OK")
            echo -e "${GREEN}[✓]${NC} $message"
            ;;
        "ISSUE")
            echo -e "${RED}[!]${NC} $message"
            ;;
        "WARN")
            echo -e "${YELLOW}[!]${NC} $message"
            ;;
        "INFO")
            echo -e "${BLUE}[i]${NC} $message"
            ;;
    esac
}

echo "=== CURRENT SYSTEM ANALYSIS ==="
echo ""

# 1. Check current DNS configuration
echo "1. DNS Configuration Analysis:"
echo "------------------------------"
print_status "INFO" "Current /etc/resolv.conf:"
cat /etc/resolv.conf | sed 's/^/   /'
echo ""

# Test DNS resolution
if timeout 5 nslookup google.com >/dev/null 2>&1; then
    print_status "OK" "DNS resolution is working"
else
    print_status "ISSUE" "DNS resolution is failing"
    print_status "INFO" "WOULD FIX: Update /etc/resolv.conf with reliable DNS servers"
fi
echo ""

# 2. Check routing table
echo "2. Routing Table Analysis:"
echo "--------------------------"
print_status "INFO" "Current default routes:"
ip route show | grep "^default" | while read route; do
    echo "   $route"
done

route_count=$(ip route show | grep "^default" | wc -l)
if [ $route_count -gt 1 ]; then
    print_status "ISSUE" "Multiple default routes detected ($route_count routes)"
    print_status "INFO" "WOULD FIX: Remove conflicting USB modem routes"
else
    print_status "OK" "Single default route (good)"
fi
echo ""

# 3. Check network interfaces
echo "3. Network Interface Analysis:"
echo "------------------------------"
print_status "INFO" "Active network interfaces:"
ip addr show | grep -E "^[0-9]+:" | while read line; do
    interface=$(echo $line | cut -d: -f2 | tr -d ' ')
    if ip addr show $interface | grep -q "inet "; then
        ip_addr=$(ip addr show $interface | grep "inet " | awk '{print $2}' | head -1)
        echo "   $interface: $ip_addr"
    fi
done

# Check for problematic USB interfaces
if ip addr show | grep -q "enx3acd9372316e\|enxb2b7a3e9b20b"; then
    print_status "ISSUE" "Problematic USB network interfaces detected"
    print_status "INFO" "WOULD FIX: Temporarily disable USB modem interfaces"
else
    print_status "OK" "No problematic USB interfaces found"
fi
echo ""

# 4. Check connectivity
echo "4. Connectivity Analysis:"
echo "-------------------------"
if timeout 5 ping -c 2 8.8.8.8 >/dev/null 2>&1; then
    print_status "OK" "Internet connectivity via IP works"
else
    print_status "ISSUE" "No internet connectivity via IP"
fi

if timeout 5 ping -c 2 google.com >/dev/null 2>&1; then
    print_status "OK" "Internet connectivity via domain works"
else
    print_status "ISSUE" "Internet connectivity via domain fails"
fi
echo ""

# 5. Check xproxy status
echo "5. XProxy Status Analysis:"
echo "--------------------------"
if pgrep -f xproxy >/dev/null; then
    print_status "INFO" "XProxy is currently running"
    print_status "INFO" "WOULD DO: Stop xproxy before making changes"
else
    print_status "INFO" "XProxy is not running"
fi

if [ -f "/etc/systemd/system/xproxy.service" ]; then
    print_status "INFO" "XProxy systemd service exists"
else
    print_status "INFO" "No XProxy systemd service found"
fi
echo ""

echo "=== SAFETY ANALYSIS ==="
echo ""

# Check what files would be backed up
echo "Files that would be backed up:"
echo "------------------------------"
if [ -f "/etc/resolv.conf" ]; then
    print_status "OK" "/etc/resolv.conf exists - WOULD BACKUP"
else
    print_status "WARN" "/etc/resolv.conf not found"
fi

print_status "OK" "Routing table - WOULD BACKUP to /tmp/"
echo ""

echo "=== RECOMMENDED ACTIONS ==="
echo ""
print_status "INFO" "The fix scripts would:"
echo "   1. Backup your current DNS and routing configuration"
echo "   2. Update DNS servers to reliable ones (8.8.8.8, 8.8.4.4)"
echo "   3. Remove conflicting network routes"
echo "   4. Temporarily disable problematic USB interfaces"
echo "   5. Configure xproxy to use only eth0"
echo "   6. Create monitoring scripts"
echo ""

echo "=== SAFETY MEASURES IN SCRIPTS ==="
echo ""
print_status "OK" "All changes are backed up with timestamps"
print_status "OK" "USB interface disabling is temporary (until reboot)"
print_status "OK" "Original configurations can be restored"
print_status "OK" "Scripts check for errors before proceeding"
echo ""

echo "=== NEXT STEPS ==="
echo ""
print_status "INFO" "To proceed safely:"
echo "   1. Review this analysis"
echo "   2. Run: sudo bash xproxy_network_fix.sh"
echo "   3. If issues occur, restore from backups"
echo "   4. Reboot to restore original USB interface state"
echo ""

print_status "INFO" "Analysis complete - NO CHANGES MADE"