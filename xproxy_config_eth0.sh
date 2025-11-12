#!/bin/bash

# XProxy ETH0 Configuration Script
# This script configures xproxy to use only the eth0 interface

echo "========================================="
echo "XProxy ETH0 Configuration Tool"
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

# Find xproxy installation directory
XPROXY_DIR=""
for dir in /opt/xproxy /usr/local/xproxy /home/*/xproxy; do
    if [ -d "$dir" ]; then
        XPROXY_DIR="$dir"
        break
    fi
done

if [ -z "$XPROXY_DIR" ]; then
    print_status "FAIL" "XProxy installation directory not found"
    print_status "INFO" "Please specify the xproxy directory manually"
    exit 1
fi

print_status "OK" "Found XProxy directory: $XPROXY_DIR"
echo ""

# 1. Stop xproxy service
echo "1. Stopping XProxy:"
echo "-------------------"
if systemctl is-active --quiet xproxy 2>/dev/null; then
    systemctl stop xproxy && \
        print_status "OK" "Stopped xproxy service" || \
        print_status "WARN" "Could not stop xproxy service"
elif pgrep -f xproxy >/dev/null 2>&1; then
    pkill -f xproxy && \
        print_status "OK" "Stopped xproxy process" || \
        print_status "WARN" "Could not stop xproxy process"
    sleep 3
else
    print_status "INFO" "XProxy was not running"
fi
echo ""

# 2. Backup existing configuration
echo "2. Backing up configuration:"
echo "----------------------------"
if [ -f "$XPROXY_DIR/config.json" ]; then
    cp "$XPROXY_DIR/config.json" "$XPROXY_DIR/config.json.backup.$(date +%Y%m%d_%H%M%S)" && \
        print_status "OK" "Backed up config.json" || \
        print_status "WARN" "Could not backup config.json"
fi

if [ -f "$XPROXY_DIR/settings.ini" ]; then
    cp "$XPROXY_DIR/settings.ini" "$XPROXY_DIR/settings.ini.backup.$(date +%Y%m%d_%H%M%S)" && \
        print_status "OK" "Backed up settings.ini" || \
        print_status "WARN" "Could not backup settings.ini"
fi
echo ""

# 3. Get eth0 information
echo "3. Analyzing ETH0 interface:"
echo "----------------------------"
ETH0_IP=$(ip addr show eth0 | grep "inet " | awk '{print $2}' | cut -d'/' -f1 | head -1)
ETH0_GATEWAY=$(ip route show | grep "default via.*dev eth0" | awk '{print $3}' | head -1)

if [ -n "$ETH0_IP" ]; then
    print_status "OK" "ETH0 IP: $ETH0_IP"
else
    print_status "FAIL" "ETH0 has no IP address"
    exit 1
fi

if [ -n "$ETH0_GATEWAY" ]; then
    print_status "OK" "ETH0 Gateway: $ETH0_GATEWAY"
else
    print_status "WARN" "ETH0 gateway not found"
fi
echo ""

# 4. Create optimized xproxy configuration
echo "4. Creating ETH0-only configuration:"
echo "------------------------------------"

# Create a configuration that forces xproxy to use only eth0
cat > "$XPROXY_DIR/eth0_config.json" << EOF
{
    "general": {
        "interface_binding": "eth0",
        "preferred_interface": "eth0",
        "interface_whitelist": ["eth0"],
        "interface_blacklist": ["enx3acd9372316e", "enxb2b7a3e9b20b"],
        "bind_to_interface": true,
        "force_interface": "eth0"
    },
    "network": {
        "primary_interface": "eth0",
        "backup_interfaces": [],
        "interface_priority": ["eth0"],
        "disable_auto_detection": true,
        "manual_interface_config": true
    },
    "dns": {
        "servers": ["8.8.8.8", "8.8.4.4", "1.1.1.1"],
        "timeout": 5,
        "retries": 3,
        "use_system_dns": false
    },
    "connection": {
        "timeout": 30,
        "retry_attempts": 3,
        "retry_delay": 5,
        "keep_alive": true
    }
}
EOF

print_status "OK" "Created ETH0-specific configuration"

# Create environment file for interface binding
cat > "$XPROXY_DIR/eth0_env" << EOF
# Force xproxy to use only eth0 interface
export XPROXY_INTERFACE=eth0
export XPROXY_BIND_INTERFACE=eth0
export XPROXY_PRIMARY_INTERFACE=eth0
export CURL_INTERFACE=eth0
export REQUESTS_CA_BUNDLE=""
EOF

print_status "OK" "Created environment configuration"
echo ""

# 5. Create startup script with interface binding
echo "5. Creating ETH0 startup script:"
echo "--------------------------------"
cat > "$XPROXY_DIR/start_eth0.sh" << EOF
#!/bin/bash

# XProxy ETH0 Startup Script
echo "Starting XProxy with ETH0 interface binding..."

# Source environment variables
source "$XPROXY_DIR/eth0_env"

# Ensure eth0 is up
ip link set eth0 up 2>/dev/null

# Disable problematic interfaces
for iface in enx3acd9372316e enxb2b7a3e9b20b; do
    if ip link show \$iface >/dev/null 2>&1; then
        echo "Disabling interface: \$iface"
        ip link set \$iface down 2>/dev/null
    fi
done

# Set up proper routing for eth0
if [ -n "$ETH0_GATEWAY" ]; then
    # Remove any conflicting default routes
    ip route del default via 192.168.107.1 dev enx3acd9372316e 2>/dev/null
    ip route del default via 192.168.108.1 dev enxb2b7a3e9b20b 2>/dev/null
    
    # Ensure eth0 default route exists
    if ! ip route show | grep -q "default via $ETH0_GATEWAY dev eth0"; then
        ip route add default via $ETH0_GATEWAY dev eth0 metric 100
    fi
fi

# Start xproxy with interface binding
cd "$XPROXY_DIR"
if [ -f "./xproxy" ]; then
    echo "Starting xproxy with ETH0 binding..."
    ./xproxy --config=eth0_config.json --interface=eth0 --bind-interface=eth0
elif [ -f "./bin/xproxy" ]; then
    echo "Starting xproxy from bin directory..."
    ./bin/xproxy --config=eth0_config.json --interface=eth0 --bind-interface=eth0
else
    echo "XProxy executable not found!"
    exit 1
fi
EOF

chmod +x "$XPROXY_DIR/start_eth0.sh"
print_status "OK" "Created ETH0 startup script"
echo ""

# 6. Create systemd service for ETH0-only xproxy
echo "6. Creating systemd service:"
echo "----------------------------"
cat > /etc/systemd/system/xproxy-eth0.service << EOF
[Unit]
Description=XProxy ETH0 Service
After=network.target
Wants=network.target

[Service]
Type=simple
User=root
WorkingDirectory=$XPROXY_DIR
Environment=XPROXY_INTERFACE=eth0
Environment=XPROXY_BIND_INTERFACE=eth0
ExecStartPre=/bin/bash -c 'ip link set eth0 up'
ExecStartPre=/bin/bash -c 'for iface in enx3acd9372316e enxb2b7a3e9b20b; do ip link set \$iface down 2>/dev/null || true; done'
ExecStart=$XPROXY_DIR/start_eth0.sh
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload && \
    print_status "OK" "Created xproxy-eth0 systemd service" || \
    print_status "WARN" "Could not create systemd service"
echo ""

# 7. Test configuration
echo "7. Testing configuration:"
echo "-------------------------"

# Test if eth0 is accessible
if ping -c 2 -W 3 -I eth0 8.8.8.8 >/dev/null 2>&1; then
    print_status "OK" "ETH0 interface can reach internet"
else
    print_status "WARN" "ETH0 interface connectivity test failed"
fi

# Test DNS through eth0
if timeout 10 dig @8.8.8.8 +tcp google.com >/dev/null 2>&1; then
    print_status "OK" "DNS resolution works"
else
    print_status "WARN" "DNS resolution test failed"
fi
echo ""

# 8. Final instructions
echo "8. Setup complete!"
echo "==================="
print_status "INFO" "XProxy is now configured to use only ETH0 interface"
echo ""
print_status "INFO" "To start XProxy with ETH0 binding:"
echo "   sudo systemctl start xproxy-eth0"
echo ""
print_status "INFO" "To enable auto-start on boot:"
echo "   sudo systemctl enable xproxy-eth0"
echo ""
print_status "INFO" "To monitor XProxy logs:"
echo "   sudo journalctl -u xproxy-eth0 -f"
echo ""
print_status "INFO" "Manual start option:"
echo "   sudo $XPROXY_DIR/start_eth0.sh"
echo ""
print_status "WARN" "Remember to disable the old xproxy service:"
echo "   sudo systemctl disable xproxy"
echo "   sudo systemctl stop xproxy"
echo ""
echo "========================================="