#!/bin/bash

# XProxy Network Fix Script
# This script fixes DNS resolution and routing issues affecting xproxy

echo "========================================="
echo "XProxy Network Fix Tool"
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

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    print_status "FAIL" "This script must be run as root (use sudo)"
    exit 1
fi

print_status "INFO" "Starting network fixes..."
echo ""

# 1. Backup current configuration
echo "1. Creating backups:"
echo "--------------------"
cp /etc/resolv.conf /etc/resolv.conf.backup.$(date +%Y%m%d_%H%M%S) 2>/dev/null && \
    print_status "OK" "Backed up /etc/resolv.conf" || \
    print_status "WARN" "Could not backup /etc/resolv.conf"

ip route show > /tmp/routes.backup.$(date +%Y%m%d_%H%M%S) && \
    print_status "OK" "Backed up routing table" || \
    print_status "WARN" "Could not backup routing table"
echo ""

# 2. Fix DNS resolution
echo "2. Fixing DNS resolution:"
echo "-------------------------"

# Stop systemd-resolved if it's interfering
if systemctl is-active --quiet systemd-resolved; then
    print_status "INFO" "Stopping systemd-resolved temporarily"
    systemctl stop systemd-resolved
fi

# Create a clean resolv.conf
cat > /etc/resolv.conf << EOF
# Fixed DNS configuration for xproxy
nameserver 8.8.8.8
nameserver 8.8.4.4
nameserver 1.1.1.1
options timeout:2
options attempts:3
EOF

print_status "OK" "Updated /etc/resolv.conf with reliable DNS servers"

# Test DNS resolution
if timeout 10 nslookup google.com >/dev/null 2>&1; then
    print_status "OK" "DNS resolution is now working"
else
    print_status "WARN" "DNS resolution still has issues"
fi
echo ""

# 3. Clean up routing table
echo "3. Cleaning up routing table:"
echo "-----------------------------"

# Remove duplicate and problematic routes
print_status "INFO" "Current default routes:"
ip route show | grep "^default" | while read route; do
    echo "   $route"
done

# Remove the USB modem route that's causing issues
if ip route show | grep -q "default via 192.168.107.1 dev enx3acd9372316e"; then
    ip route del default via 192.168.107.1 dev enx3acd9372316e 2>/dev/null && \
        print_status "OK" "Removed problematic USB modem route (192.168.107.1)" || \
        print_status "WARN" "Could not remove USB modem route"
fi

# Remove duplicate eth0 routes if they exist
duplicate_routes=$(ip route show | grep "default via 192.168.1.1 dev eth0" | wc -l)
if [ $duplicate_routes -gt 1 ]; then
    print_status "INFO" "Removing duplicate eth0 routes"
    # Keep only the route with the lowest metric
    ip route show | grep "default via 192.168.1.1 dev eth0" | tail -n +2 | while read route; do
        ip route del $route 2>/dev/null && \
            print_status "OK" "Removed duplicate route: $route"
    done
fi

print_status "INFO" "Updated routing table:"
ip route show | grep "^default" | while read route; do
    echo "   $route"
done
echo ""

# 4. Disable problematic network interfaces
echo "4. Managing network interfaces:"
echo "-------------------------------"

# Bring down the problematic USB interfaces
for iface in enx3acd9372316e enxb2b7a3e9b20b; do
    if ip link show $iface >/dev/null 2>&1; then
        if ip addr show $iface | grep -q "inet "; then
            print_status "INFO" "Bringing down interface $iface"
            ip link set $iface down 2>/dev/null && \
                print_status "OK" "Interface $iface is down" || \
                print_status "WARN" "Could not bring down $iface"
        fi
    fi
done

# Ensure eth0 is up and working
if ip link show eth0 >/dev/null 2>&1; then
    ip link set eth0 up 2>/dev/null
    if ip addr show eth0 | grep -q "inet "; then
        print_status "OK" "Interface eth0 is up and has IP address"
    else
        print_status "WARN" "Interface eth0 is up but has no IP address"
    fi
fi
echo ""

# 5. Restart network services
echo "5. Restarting network services:"
echo "-------------------------------"

# Restart networking
if command -v systemctl >/dev/null 2>&1; then
    systemctl restart networking 2>/dev/null && \
        print_status "OK" "Restarted networking service" || \
        print_status "WARN" "Could not restart networking service"
    
    # Restart systemd-resolved with proper configuration
    systemctl restart systemd-resolved 2>/dev/null && \
        print_status "OK" "Restarted systemd-resolved" || \
        print_status "WARN" "Could not restart systemd-resolved"
fi
echo ""

# 6. Test connectivity after fixes
echo "6. Testing connectivity after fixes:"
echo "------------------------------------"

# Test basic connectivity
if ping -c 3 -W 5 8.8.8.8 >/dev/null 2>&1; then
    print_status "OK" "Can ping 8.8.8.8"
else
    print_status "FAIL" "Cannot ping 8.8.8.8"
fi

# Test DNS resolution
if timeout 10 nslookup google.com >/dev/null 2>&1; then
    print_status "OK" "DNS resolution works"
else
    print_status "FAIL" "DNS resolution still fails"
fi

# Test HTTP connectivity
if timeout 10 curl -s http://google.com >/dev/null 2>&1; then
    print_status "OK" "HTTP connectivity works"
else
    print_status "FAIL" "HTTP connectivity fails"
fi
echo ""

# 7. XProxy specific fixes
echo "7. XProxy configuration:"
echo "------------------------"

# Stop xproxy if running
if pgrep -f xproxy >/dev/null 2>&1; then
    print_status "INFO" "Stopping xproxy"
    pkill -f xproxy 2>/dev/null
    sleep 2
fi

# Clear xproxy cache/temp files if they exist
if [ -d /opt/xproxy/tmp ]; then
    rm -rf /opt/xproxy/tmp/* 2>/dev/null && \
        print_status "OK" "Cleared xproxy temp files"
fi

print_status "INFO" "XProxy should now use only eth0 interface"
echo ""

# 8. Create persistent configuration
echo "8. Making changes persistent:"
echo "----------------------------"

# Create a script to disable USB interfaces on boot
cat > /etc/rc.local << 'EOF'
#!/bin/bash
# Disable problematic USB network interfaces
for iface in enx3acd9372316e enxb2b7a3e9b20b; do
    if ip link show $iface >/dev/null 2>&1; then
        ip link set $iface down
    fi
done
exit 0
EOF

chmod +x /etc/rc.local 2>/dev/null && \
    print_status "OK" "Created persistent interface configuration" || \
    print_status "WARN" "Could not create persistent configuration"

echo ""
echo "========================================="
echo "Network fixes completed!"
echo "========================================="
echo ""
print_status "INFO" "Next steps:"
echo "1. Restart xproxy service"
echo "2. Monitor xproxy logs for improvements"
echo "3. Run the diagnostic script to verify fixes"
echo ""
print_status "INFO" "To restart xproxy:"
echo "   sudo systemctl restart xproxy"
echo "   OR"
echo "   sudo /opt/xproxy/xproxy &"