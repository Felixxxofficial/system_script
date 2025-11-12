#!/bin/bash

# XProxy Restore Script
# This script restores your system to the state before running the fix scripts

echo "========================================="
echo "XProxy Configuration Restore Tool"
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

print_status "INFO" "Starting system restore..."
echo ""

# 1. Restore DNS configuration
echo "1. Restoring DNS Configuration:"
echo "-------------------------------"

# Find the most recent backup
latest_resolv_backup=$(ls -t /etc/resolv.conf.backup.* 2>/dev/null | head -1)

if [ -n "$latest_resolv_backup" ]; then
    cp "$latest_resolv_backup" /etc/resolv.conf && \
        print_status "OK" "Restored /etc/resolv.conf from $latest_resolv_backup" || \
        print_status "FAIL" "Failed to restore /etc/resolv.conf"
else
    print_status "WARN" "No resolv.conf backup found"
    print_status "INFO" "Creating default resolv.conf"
    cat > /etc/resolv.conf << EOF
# Default DNS configuration
nameserver 127.0.0.53
options edns0 trust-ad
search .
EOF
fi
echo ""

# 2. Restore systemd-resolved if it was running
echo "2. Restoring DNS Services:"
echo "--------------------------"
if systemctl is-enabled systemd-resolved >/dev/null 2>&1; then
    systemctl start systemd-resolved && \
        print_status "OK" "Restarted systemd-resolved" || \
        print_status "WARN" "Could not restart systemd-resolved"
else
    print_status "INFO" "systemd-resolved was not enabled"
fi
echo ""

# 3. Re-enable network interfaces
echo "3. Re-enabling Network Interfaces:"
echo "-----------------------------------"

# Re-enable USB interfaces that might have been disabled
for interface in enx3acd9372316e enxb2b7a3e9b20b; do
    if ip link show $interface >/dev/null 2>&1; then
        ip link set $interface up && \
            print_status "OK" "Re-enabled interface $interface" || \
            print_status "WARN" "Could not re-enable $interface"
    fi
done
echo ""

# 4. Restore routing (reboot recommended)
echo "4. Routing Table Restoration:"
echo "-----------------------------"
print_status "INFO" "Routing table changes require network restart"
print_status "INFO" "Recommended: sudo systemctl restart networking"
print_status "INFO" "Or reboot the system for complete restoration"
echo ""

# 5. Stop custom xproxy services
echo "5. Cleaning Up Custom Services:"
echo "-------------------------------"

# Stop and disable custom xproxy service if it exists
if systemctl is-active xproxy-eth0 >/dev/null 2>&1; then
    systemctl stop xproxy-eth0 && \
        print_status "OK" "Stopped xproxy-eth0 service" || \
        print_status "WARN" "Could not stop xproxy-eth0 service"
fi

if systemctl is-enabled xproxy-eth0 >/dev/null 2>&1; then
    systemctl disable xproxy-eth0 && \
        print_status "OK" "Disabled xproxy-eth0 service" || \
        print_status "WARN" "Could not disable xproxy-eth0 service"
fi

# Remove custom service file
if [ -f "/etc/systemd/system/xproxy-eth0.service" ]; then
    rm -f /etc/systemd/system/xproxy-eth0.service && \
        print_status "OK" "Removed custom xproxy service file" || \
        print_status "WARN" "Could not remove service file"
    systemctl daemon-reload
fi
echo ""

# 6. Clean up custom configurations
echo "6. Cleaning Up Custom Configurations:"
echo "-------------------------------------"

# Remove custom xproxy configurations
if [ -d "/opt/xproxy-eth0" ]; then
    rm -rf /opt/xproxy-eth0 && \
        print_status "OK" "Removed custom xproxy configuration" || \
        print_status "WARN" "Could not remove custom configuration"
fi

# Remove startup scripts
if [ -f "/usr/local/bin/start_xproxy_eth0.sh" ]; then
    rm -f /usr/local/bin/start_xproxy_eth0.sh && \
        print_status "OK" "Removed custom startup script" || \
        print_status "WARN" "Could not remove startup script"
fi
echo ""

# 7. Remove rc.local modifications
echo "7. Cleaning Up Boot Scripts:"
echo "----------------------------"
if [ -f "/etc/rc.local" ]; then
    # Remove lines added by our scripts
    sed -i '/# Disable problematic USB network interfaces/d' /etc/rc.local
    sed -i '/ip link set enx3acd9372316e down/d' /etc/rc.local
    sed -i '/ip link set enxb2b7a3e9b20b down/d' /etc/rc.local
    print_status "OK" "Cleaned up /etc/rc.local"
fi
echo ""

echo "=== RESTORATION SUMMARY ==="
echo ""
print_status "OK" "DNS configuration restored"
print_status "OK" "Network interfaces re-enabled"
print_status "OK" "Custom services removed"
print_status "OK" "Custom configurations cleaned up"
echo ""

print_status "INFO" "IMPORTANT: To complete restoration:"
echo "   1. Restart networking: sudo systemctl restart networking"
echo "   2. Or reboot the system: sudo reboot"
echo "   3. Check that your original xproxy configuration works"
echo ""

print_status "INFO" "Your system should now be back to its original state"