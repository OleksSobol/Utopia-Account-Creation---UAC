#!/bin/bash
# deploy_systemd_service.sh - Deploy updated systemd service configuration

echo "🔧 Deploying updated systemd service configuration..."

# Stop the current service
echo "Stopping current service..."
sudo systemctl stop api_callback.service

# Copy the new service file
echo "Installing new service configuration..."
sudo cp api_callback.service /etc/systemd/system/

# Reload systemd
echo "Reloading systemd daemon..."
sudo systemctl daemon-reload

# Enable and start the service
echo "Enabling and starting service..."
sudo systemctl enable api_callback.service
sudo systemctl start api_callback.service

# Check status
echo "Service status:"
sudo systemctl status api_callback.service --no-pager -l

echo "✅ Service deployment complete!"