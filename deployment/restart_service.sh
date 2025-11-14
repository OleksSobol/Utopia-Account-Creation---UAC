#!/bin/bash
# restart_service.sh - Reliable service restart script

echo "🔄 Restarting UAC API Callback Service..."

# Try graceful stop first
echo "Attempting graceful stop..."
sudo systemctl stop api_callback.service

# Wait a few seconds
sleep 3

# Check if still running
if systemctl is-active --quiet api_callback.service; then
    echo "⚠️ Graceful stop failed, force killing..."
    
    # Force kill the service
    sudo systemctl kill api_callback.service
    sleep 2
    
    # Kill any remaining uwsgi processes
    sudo pkill -f "uwsgi.*api_callback"
    sleep 1
    
    # Reset failed state
    sudo systemctl reset-failed api_callback.service
fi

# Make sure it's stopped
echo "Verifying service is stopped..."
sudo systemctl status api_callback.service --no-pager -l

# Start the service
echo "Starting service..."
sudo systemctl start api_callback.service

# Wait a moment for startup
sleep 2

# Check status
echo "Final status:"
sudo systemctl status api_callback.service --no-pager -l

echo "✅ Restart complete!"