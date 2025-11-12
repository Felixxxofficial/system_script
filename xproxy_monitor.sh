#!/bin/bash

# XProxy Monitoring Script
# This script monitors xproxy status and restarts it if needed

echo "========================================="
echo "XProxy Monitoring Tool"
echo "========================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
MONITOR_INTERVAL=30  # Check every 30 seconds
LOG_FILE="/var/log/xproxy_monitor.log"
MAX_RESTART_ATTEMPTS=3
RESTART_COOLDOWN=300  # 5 minutes between restart attempts

# Function to print colored output
print_status() {
    local status=$1
    local message=$2
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    case $status in
        "OK")
            echo -e "${GREEN}[✓]${NC} [$timestamp] $message"
            echo "[$timestamp] [OK] $message" >> "$LOG_FILE"
            ;;
        "FAIL")
            echo -e "${RED}[✗]${NC} [$timestamp] $message"
            echo "[$timestamp] [FAIL] $message" >> "$LOG_FILE"
            ;;
        "WARN")
            echo -e "${YELLOW}[!]${NC} [$timestamp] $message"
            echo "[$timestamp] [WARN] $message" >> "$LOG_FILE"
            ;;
        "INFO")
            echo -e "${BLUE}[i]${NC} [$timestamp] $message"
            echo "[$timestamp] [INFO] $message" >> "$LOG_FILE"
            ;;
    esac
}

# Function to check if xproxy is running
check_xproxy_running() {
    if systemctl is-active --quiet xproxy-eth0 2>/dev/null; then
        return 0
    elif systemctl is-active --quiet xproxy 2>/dev/null; then
        return 0
    elif pgrep -f xproxy >/dev/null 2>&1; then
        return 0
    else
        return 1
    fi
}

# Function to check xproxy connectivity
check_xproxy_connectivity() {
    # Check if xproxy log shows recent successful connections
    local log_file="/opt/xproxy/log/xproxy.log"
    if [ -f "$log_file" ]; then
        # Check for recent errors (last 5 minutes)
        local recent_errors=$(tail -100 "$log_file" | grep "$(date '+%d/%m/%Y %H:%M' -d '5 minutes ago')" | grep -c "connect failed\|timed out\|ERROR")
        if [ $recent_errors -gt 10 ]; then
            return 1  # Too many recent errors
        fi
        
        # Check for successful connections
        local recent_success=$(tail -100 "$log_file" | grep "$(date '+%d/%m/%Y %H:%M' -d '2 minutes ago')" | grep -c "Request completed\|Authenticated successfully")
        if [ $recent_success -gt 0 ]; then
            return 0  # Recent successful activity
        fi
    fi
    
    # Test basic connectivity through xproxy
    if timeout 10 curl -s --proxy localhost:8080 http://google.com >/dev/null 2>&1; then
        return 0
    else
        return 1
    fi
}

# Function to check network connectivity
check_network_connectivity() {
    # Check if eth0 is up and has connectivity
    if ! ip addr show eth0 | grep -q "inet "; then
        return 1
    fi
    
    # Test basic internet connectivity
    if ! ping -c 2 -W 3 8.8.8.8 >/dev/null 2>&1; then
        return 1
    fi
    
    # Test DNS resolution
    if ! timeout 5 nslookup google.com >/dev/null 2>&1; then
        return 1
    fi
    
    return 0
}

# Function to restart xproxy
restart_xproxy() {
    local restart_method=$1
    
    print_status "INFO" "Attempting to restart xproxy using method: $restart_method"
    
    case $restart_method in
        "systemd-eth0")
            systemctl stop xproxy-eth0 2>/dev/null
            sleep 5
            systemctl start xproxy-eth0 2>/dev/null
            ;;
        "systemd")
            systemctl stop xproxy 2>/dev/null
            sleep 5
            systemctl start xproxy 2>/dev/null
            ;;
        "manual")
            pkill -f xproxy 2>/dev/null
            sleep 5
            if [ -f "/opt/xproxy/start_eth0.sh" ]; then
                /opt/xproxy/start_eth0.sh &
            elif [ -f "/opt/xproxy/xproxy" ]; then
                cd /opt/xproxy && ./xproxy &
            fi
            ;;
    esac
    
    sleep 10  # Wait for startup
    
    if check_xproxy_running; then
        print_status "OK" "XProxy restarted successfully"
        return 0
    else
        print_status "FAIL" "XProxy restart failed"
        return 1
    fi
}

# Function to fix network issues
fix_network_issues() {
    print_status "INFO" "Attempting to fix network issues"
    
    # Ensure eth0 is up
    ip link set eth0 up 2>/dev/null
    
    # Disable problematic interfaces
    for iface in enx3acd9372316e enxb2b7a3e9b20b; do
        if ip link show $iface >/dev/null 2>&1; then
            ip link set $iface down 2>/dev/null
        fi
    done
    
    # Fix DNS if needed
    if ! timeout 5 nslookup google.com >/dev/null 2>&1; then
        echo "nameserver 8.8.8.8" > /etc/resolv.conf
        echo "nameserver 8.8.4.4" >> /etc/resolv.conf
        systemctl restart systemd-resolved 2>/dev/null
    fi
    
    # Clean up routing table
    ip route del default via 192.168.107.1 dev enx3acd9372316e 2>/dev/null
    ip route del default via 192.168.108.1 dev enxb2b7a3e9b20b 2>/dev/null
}

# Main monitoring function
monitor_xproxy() {
    local restart_count=0
    local last_restart_time=0
    
    print_status "INFO" "Starting XProxy monitoring (interval: ${MONITOR_INTERVAL}s)"
    
    while true; do
        local current_time=$(date +%s)
        
        # Check if xproxy is running
        if ! check_xproxy_running; then
            print_status "FAIL" "XProxy is not running"
            
            # Check if we can restart (cooldown period)
            if [ $((current_time - last_restart_time)) -gt $RESTART_COOLDOWN ]; then
                if [ $restart_count -lt $MAX_RESTART_ATTEMPTS ]; then
                    # Try different restart methods
                    if [ $restart_count -eq 0 ]; then
                        restart_xproxy "systemd-eth0"
                    elif [ $restart_count -eq 1 ]; then
                        restart_xproxy "systemd"
                    else
                        restart_xproxy "manual"
                    fi
                    
                    restart_count=$((restart_count + 1))
                    last_restart_time=$current_time
                else
                    print_status "WARN" "Maximum restart attempts reached, waiting for manual intervention"
                    restart_count=0  # Reset after extended wait
                fi
            else
                print_status "INFO" "Waiting for cooldown period before next restart attempt"
            fi
        else
            print_status "OK" "XProxy is running"
            restart_count=0  # Reset restart count on successful check
            
            # Check connectivity
            if ! check_xproxy_connectivity; then
                print_status "WARN" "XProxy connectivity issues detected"
                
                # Check if it's a network problem
                if ! check_network_connectivity; then
                    print_status "WARN" "Network connectivity issues detected"
                    if [ "$EUID" -eq 0 ]; then
                        fix_network_issues
                    else
                        print_status "WARN" "Need root privileges to fix network issues"
                    fi
                fi
            else
                print_status "OK" "XProxy connectivity is good"
            fi
        fi
        
        sleep $MONITOR_INTERVAL
    done
}

# Function to show current status
show_status() {
    echo "XProxy Status Report:"
    echo "===================="
    
    # Check xproxy process
    if check_xproxy_running; then
        print_status "OK" "XProxy is running"
        
        # Show process details
        local pid=$(pgrep -f xproxy | head -1)
        if [ -n "$pid" ]; then
            echo "   PID: $pid"
            echo "   Memory: $(ps -p $pid -o rss= | awk '{print $1/1024 " MB"}')"
            echo "   CPU: $(ps -p $pid -o %cpu= | awk '{print $1"%"}')"
        fi
    else
        print_status "FAIL" "XProxy is not running"
    fi
    
    # Check network
    if check_network_connectivity; then
        print_status "OK" "Network connectivity is good"
    else
        print_status "FAIL" "Network connectivity issues"
    fi
    
    # Check xproxy connectivity
    if check_xproxy_connectivity; then
        print_status "OK" "XProxy connectivity is good"
    else
        print_status "WARN" "XProxy connectivity issues"
    fi
    
    # Show recent log entries
    echo ""
    echo "Recent XProxy Log Entries:"
    echo "-------------------------"
    if [ -f "/opt/xproxy/log/xproxy.log" ]; then
        tail -10 /opt/xproxy/log/xproxy.log | while read line; do
            echo "   $line"
        done
    else
        echo "   Log file not found"
    fi
}

# Main script logic
case "${1:-monitor}" in
    "monitor")
        if [ "$EUID" -ne 0 ]; then
            print_status "WARN" "Running without root privileges - some fixes may not work"
        fi
        monitor_xproxy
        ;;
    "status")
        show_status
        ;;
    "restart")
        if [ "$EUID" -ne 0 ]; then
            print_status "FAIL" "Root privileges required for restart"
            exit 1
        fi
        restart_xproxy "${2:-systemd-eth0}"
        ;;
    "fix")
        if [ "$EUID" -ne 0 ]; then
            print_status "FAIL" "Root privileges required for network fixes"
            exit 1
        fi
        fix_network_issues
        ;;
    *)
        echo "Usage: $0 [monitor|status|restart|fix]"
        echo ""
        echo "Commands:"
        echo "  monitor  - Start continuous monitoring (default)"
        echo "  status   - Show current status"
        echo "  restart  - Restart xproxy service"
        echo "  fix      - Fix network issues"
        exit 1
        ;;
esac