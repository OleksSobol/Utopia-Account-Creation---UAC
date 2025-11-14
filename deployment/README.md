# Deployment Scripts

This folder contains systemd service management scripts and configuration files for the UAC-Utopia Account Creation service.

## Files

### `api_callback.service`
- systemd service unit file for the UAC API callback service
- Configured for proper uWSGI shutdown handling
- Uses socket-based communication with nginx

### `deploy_systemd_service.sh`
- Deploys the systemd service configuration
- Stops service, copies service file, reloads systemd, and restarts service
- Use this when updating the systemd service configuration

### `restart_service.sh` 
- Reliable service restart script that handles stuck processes
- Tries graceful stop first, then force kills if necessary
- Use this for regular service restarts when deploying code changes

## Usage

### Initial Service Deployment
```bash
cd deployment
chmod +x *.sh
./deploy_systemd_service.sh
```

### Regular Service Restarts
```bash
cd deployment
./restart_service.sh
```

### Manual Service Management
```bash
# Check status
sudo systemctl status api_callback.service

# View logs
sudo journalctl -u api_callback.service -f

# Stop/start manually
sudo systemctl stop api_callback.service
sudo systemctl start api_callback.service
```

## Service Configuration Notes

- **Timeout**: Service stops within 15 seconds (TimeoutStopSec=15)
- **Process Management**: Uses mixed kill mode for reliable shutdown
- **Restart Policy**: Always restarts on failure with 5 second delay
- **User**: Runs as `gnapi` user
- **Logging**: Logs go to systemd journal (use `journalctl` to view)

## Troubleshooting

If service won't stop cleanly:
```bash
./restart_service.sh
```

If deployment fails:
```bash
# Check service file syntax
systemd-analyze verify deployment/api_callback.service

# Check current service status
sudo systemctl status api_callback.service

# View detailed logs
sudo journalctl -u api_callback.service --since "10 minutes ago"
```