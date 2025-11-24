# Utopia API Handler

A Flask-based service that integrates Utopia webhook events with PowerCode.
The service receives Utopia callbacks (webhooks), looks up or creates customers in PowerCode, assigns service plans and tickets, logs activity, and sends notification emails.

![Demo GIF showing webhook flow](assets/demo.gif)
---

## Quick Summary
- Receives webhook callbacks at `/api-callback` (POST JSON).
- Searches PowerCode for existing customers, creates customers if needed.
- Adds service plans and fees to customers.
- Creates tickets (using a template editor) and adds tags.
- Tracks failures and provides an admin UI to review/resolve them.
- Sends email notifications on success/failure.

## Features
- Webhook handler for Utopia events
- Admin UI (session-based login) for lookups, manual customer creation, ticket template editing, and failure management
- Failure tracker with REST API for listing, resolving, and deleting failure records
- Ticket template CRUD (save/load/list/delete)
- Config editor and ability to trigger service restart (production only)
- Log viewer and downloadable logs

## Repository layout
- `api_callback.py` - main Flask app and business logic (webhook, admin endpoints)
- `app/` - blueprints and route handlers (`powercode_route.py`, `utopia_route.py`)
- `deployment/` - systemd unit and helper scripts (`api_callback.service`, `deploy_systemd_service.sh`, `restart_service.sh`)
- `ticket_descriptions/` - ticket templates
- `tests/` - unit and integration tests
- `.env.example` - environment variables template (copy to `.env`)

## Requirements
- Python 3.8+
- See `requirements.txt` for Python dependencies (Flask, Flask-Mail, requests, python-dotenv, ...)

## Configuration (environment variables)
Create a `.env` in the project root by copying the example, and fill values before running.

```bash
cp .env.example .env
# Edit .env and populate required variables
```

Important variables (provide in `.env`): `PC_API_KEY`, `UTOPIA_API_KEY`, `PC_URL`, `PC_URL_TICKET`, `UTOPIA_URL_ENDPOINT`, `MAIL_SERVER`, `MAIL_PORT`, `EMAIL_SENDER`, `EMAIL_RECIPIENTS`, `CUSTOMER_PORTAL_PASSWORD`, `PC_VERIFY_SSL`, `SECRET_KEY`, etc.

Note: Never commit `.env` to source control.

## Running locally (development)
1. Install dependencies:

```powershell
cd e:\workspace\work_projects\globalnet\UAC-Utopia-Account-Creation
pip install -r requirements.txt
```

2. Copy `.env.example` and edit values:

```powershell
cp .env.example .env
# edit .env with a text editor
```

3. Start the app (development server):

```powershell
python api_callback.py
```

Open `http://localhost:5050` for the admin UI. The Flask dev server is used only for development and debugging.

Important: `api_callback.py` currently calls `app.run(..., debug=True)` in development — set `debug=False` or use a production WSGI server for production.

## Testing
Run tests with `pytest` from the project root:

```powershell
pip install -r requirements.txt
pytest -q
```

## Webhook usage and testing
The webhook expects JSON POST requests to `/api-callback`. Example quick test using `curl`:

```bash
curl -X POST http://localhost:5050/api-callback \
  -H "Content-Type: application/json" \
  -d '{"event":"Project New Order","orderref":"ABC123","msg":"Project New Order"}'
```

The app will fetch order details from Utopia (using `Utopia.getCustomerFromUtopia(orderref)`), then process the order.

## Admin UI
- `/login` - login page (session-based). Credentials are managed in `users.json` and via config admin credentials.
- `/admin` - lookup/creation UI
- `/admin/failures` - failure management UI
- `/admin/ticket-editor` - edit ticket templates
- `/admin/config` - view/edit environment-backed configuration (requires appropriate user permissions)

## Logging
Logs are written to the file configured by `LOG_FILE` in `config.py` (often `api_class.log` or similar). Use the log viewer in the admin UI or tail the file on the server:

```bash
tail -f /path/to/api_class.log
```

## Deployment (recommended production approach)
This project includes a `deployment/` directory with a systemd unit and helper scripts. Production should run under a WSGI server (gunicorn, uWSGI) and be managed by systemd.

Typical production deploy steps (on the server):

```bash
ssh deploy@your-server
cd /srv/utopia-api  # or whatever path you use
git pull origin main
cp .env.production .env   # populate production env file securely
sudo systemctl daemon-reload
sudo systemctl restart api_callback.service
sudo journalctl -u api_callback -f
```

If you update the unit file (`deployment/api_callback.service`), run `sudo systemctl daemon-reload` before restarting.

Note: README previously referenced `./deploy_changes_UAC.sh`. The current `deployment/` folder contains `deploy_systemd_service.sh` — update your docs or add a wrapper script to match your workflow.

## Security recommendations
- Do not run the Flask dev server (`debug=True`) in production.
- Enable SSL verification for external APIs (`PC_VERIFY_SSL=true`) and fix certificates on the PowerCode side.
- Harden the webhook endpoint: require an HMAC signature or API key header and verify it.
- Ensure the `login_required` decorator is fully implemented and applied to all sensitive routes.
- Do not log secrets (API keys, full passwords). Review logging calls.

## Failure tracking
Failures are stored/managed by `FailureTracker` (see `failure_tracker.py`) and surfaced in the admin UI. Endpoints include:

- `GET /api/failures` - list failures
- `POST /api/failures/<orderref>/resolve` - resolve a failure
- `DELETE /api/failures/<orderref>/delete` - delete a failure

## Ticket templates
Templates live in `ticket_descriptions/`. The admin UI provides save/load/list/delete operations. Templates are used to populate ticket descriptions when creating tickets in PowerCode.

## Creating a demo GIF for GitHub
To showcase the app on GitHub, record a short demo GIF (e.g., login, run a webhook test, see logs). Below are reliable ways to create a GIF from a terminal session or screen recording.

Option A — Record terminal session with `asciinema` + convert to GIF

1. Install tools (on Linux):

```bash
# install asciinema
sudo apt install -y asciinema
# pip-based converter
pip install asciinema2gif
```

2. Record the session (run commands that show the app start and a curl to `/api-callback`):

```bash
asciinema rec demo.cast
# perform commands (start app, run curl, show logs)
# Press Ctrl-D or type exit to finish recording
```

3. Convert to GIF:

```bash
asciinema2gif demo.cast demo.gif
```

Option B — Use `svg-term-cli` to capture an asciicast and convert to GIF

1. Record with `asciinema` like above.
2. Convert to SVG (on a machine with Node.js):

```bash
npm install -g svg-term-cli
svg-term --in demo.cast --out demo.svg --window --profile boxy
```

3. Convert SVG to GIF (ImageMagick/ffmpeg):

```bash
convert demo.svg demo.gif
# or using ffmpeg if you produce a sequence
```

Option C — Screen recording to GIF (GUI)

Use `peek` (Linux) or `Gifox`/`LICEcap` (macOS/Windows) to select an area and record a short clip. Save as `.gif`.

General notes for GIFs
- Keep GIFs short (3–8 seconds) and small (optimize with `gifsicle` or `ffmpeg` conversions).
- Place the GIF into the repo, e.g. `assets/demo.gif`, commit and reference in README using Markdown:

```markdown
![Quick demo of Utopia API Handler](assets/demo.gif)
```

To optimize:

```bash
# Reduce colors and resize
gifsicle --optimize=3 --colors 64 demo.gif -o demo.opt.gif
```

## Adding the GIF to this repository
1. Create `assets/` at repo root and copy `demo.gif` there.
2. Commit and push:

```bash
git add assets/demo.gif
git commit -m "docs: add demo GIF showing webhook and admin UI" 
git push origin main
```

3. Reference the GIF in the README above the Quick Start or Usage section.

## Contributing
- Follow existing style. Run tests and lint locally before submitting PRs.

## Troubleshooting
- If the app prints `Missing required environment variables`, ensure `.env` contains all required keys.
- If `No module named 'dotenv'`, run `pip install python-dotenv`.
- For SSL errors with PowerCode, prefer fixing certs and enabling `PC_VERIFY_SSL=true` rather than disabling verification.

## Contact / Maintainers
Open issues or PRs on the GitHub repository for bugs and feature requests.

---

If you want, I can:
- (A) add a small `assets/demo.gif` placeholder and update the README to embed it, or
- (B) generate a demo cast script you can run locally to produce a GIF, or
- (C) update deployment instructions to include exact `systemctl` commands for your server.

Tell me which you prefer and I will proceed.
# Utopia API Handler

This Python project is designed to handle customer data integration between Utopia and PowerCode through an API. It processes orders from Utopia, searches for customers in PowerCode, and creates customer records in PowerCode if they do not exist. Additionally, it assigns service plans and sends notification emails.

## Features

1. **API Endpoint**: Handles incoming API callbacks from Utopia.
2. **Customer Management**: Searches for customers in PowerCode, creates new records if not found.
3. **Service Plan Assignment**: Adds appropriate service plans from Utopia and additional manual plans.
4. **Email Notifications**: Sends emails for success or failure.
5. **Logging**: Logs actions and errors to `api_class.log`.

## Requirements

- Python 3.x
- Flask
- Flask-Mail
- Requests
- python-dotenv
- Utopia and PowerCode Python modules (custom imports)

## Configuration Setup

### Environment Variables

This application uses environment variables for secure configuration management. **Never commit the `.env` file to version control!**

### Initial Setup

1. **Copy the example environment file:**
   ```bash
   cp .env.example .env
   ```

2. **Edit `.env` and fill in the actual values for your environment**

3. **Verify all required variables are set** (see table below)

### Required Environment Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `PC_API_KEY` | PowerCode API authentication key | `your_api_key_here` |
| `UTOPIA_API_KEY` | Utopia API authentication key | `your_api_key_here` |
| `PC_URL` | PowerCode base URL | `https://example.com` |
| `PC_URL_TICKET` | PowerCode ticket API endpoint | `https://example.com:444/api/1/index.php` |
| `UTOPIA_URL_ENDPOINT` | Utopia API base URL | `https://api.utopiafiber.com` |
| `MAIL_SERVER` | SMTP mail server | `MAIL SERVER` |
| `MAIL_PORT` | SMTP port | `25` |
| `EMAIL_SENDER` | From address for emails | `no-reply@theglobal.net` |
| `EMAIL_RECIPIENTS` | Comma-separated list of recipients | `email1@example.com,email2@example.com` |
| `CUSTOMER_PORTAL_PASSWORD` | Default customer portal password | `DEFAULT_PASSWORD` |
| `PC_VERIFY_SSL` | Enable SSL verification for PowerCode API | `false` (use `true` when certs are fixed) |

### Security Notes

- **Never commit `.env` to version control** - it contains sensitive credentials
- The `.env.example` file is safe to commit (it has no real secrets)
- Use strong passwords in production environments
- The `.gitignore` file is configured to prevent `.env` from being committed

### SSL Configuration

The application supports configurable SSL verification:
- Set `PC_VERIFY_SSL=true` to enable SSL verification (recommended when certificates are valid)
- Set `PC_VERIFY_SSL=false` to disable SSL verification (only if PowerCode has certificate issues)
- A warning will be logged when SSL verification is disabled

## Setup and Installation

1. **Clone the repository and navigate to the directory**

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment variables:**
   ```bash
   cp .env.example .env
   # Edit .env and fill in your actual credentials
   ```

4. **Verify configuration:**
   ```bash
   python -c "import config; print('Config loaded successfully')"
   ```
   You should see: `✓ All required environment variables loaded successfully`


## How to Run

### Development Mode

1. **Ensure `.env` file is configured** (see Configuration Setup above)

2. **Run the Flask application:**
   ```bash
   python api_callback.py
   ```

3. **The application will start on** `http://localhost:5050`

4. **You should see:**
   ```
   ✓ All required environment variables loaded successfully
   * Running on http://127.0.0.1:5050
   ```

**Note:** The "development server" warning is normal and expected for local testing.

### Production Deployment

For production deployment on Linux servers, use the deployment script:

```bash
./deploy_changes_UAC.sh
```

This will pull the latest changes and restart the service.

## API Endpoints
/api-callback: Accepts POST requests from Utopia containing customer order data.

## Service Plan Management
The system allows for flexible service plan assignment:

Utopia Plans: These are mapped in the service_plan_mapping dictionary based on the plan description.
Additional Plans: You can manually assign extra service plans using the additional_service_plan_mapping.

## Example Callback
When Utopia sends a "Project New Order" event, the following happens:

The customer is searched in PowerCode.
If the customer doesn't exist, they are created.
A service plan is assigned based on the order details.
An email is sent to notify about the customer creation.

## Logging
All API events and errors are logged to api_class.log for audit and troubleshooting.

## Error Handling
If there are errors in customer creation or service plan assignment, an email will be sent to the recipients specified with details of the issue.


## Deployment Checklist

Before deploying to production:

- [ ] Copy `.env.example` to `.env`
- [ ] Fill in all required environment variables with actual values
- [ ] Test application startup locally (check for validation success message)
- [ ] Verify API endpoints work correctly
- [ ] Confirm email notifications are sent properly
- [ ] Check SSL certificate settings (`PC_VERIFY_SSL`)
- [ ] Review logs for any warnings or errors
- [ ] Ensure `.env` file is NOT committed to Git
- [ ] Update production server's `.env` file with production credentials

---

## Editing Ticket Description & Deploying Changes

This guide will walk you through the process of editing the ticket description and deploying changes to the system.

### Steps:

#### 1. **Edit the Ticket Description on GitHub**
1. Navigate to the `ticket_descriptions` folder.
2. Edit the `new_desc.txt` file as needed.
3. Commit and push the changes to the repository.

#### 2. **Deploy the Changes on the Server**

After editing the ticket description, you need to pull the changes to the server and restart the service.

##### Steps to deploy:

1. **SSH into the server:**
   ```bash
   ssh your-username@your-server-ip

2. **Simply run deploy_changes_UAC.sh:**
   ```bash
   ./deploy_changes_UAC.sh
The output should indicate that the service is running. If there are any issues, review the logs for troubleshooting.



## Editing Constants & Deploying Changes

**IMPORTANT:** As of Phase 1 security improvements, constants are now managed via environment variables.

### Steps to Update Configuration:

#### 1. **Edit Environment Variables**

**For Development:**
1. Edit your local `.env` file
2. Update the relevant variable (e.g., `EMAIL_RECIPIENTS`, `MAIL_SERVER`, etc.)
3. Restart the application

**For Production:**
1. SSH into the server
2. Edit `/path/to/application/.env` file
3. Update the variable
4. Run the deployment script to restart the service

#### 2. **Deploy the Changes on the Server**

1. **SSH into the server:**
   ```bash
   ssh your-username@your-server-ip
   ```

2. **Run the deployment script:**
   ```bash
   ./deploy_changes_UAC.sh
   ```

**Note:** You no longer need to edit `config.py` or `static_vars.py` directly. All configuration is managed through the `.env` file for security and flexibility.

### Common Configuration Changes

| What to Change | Environment Variable | Example |
|----------------|---------------------|---------|
| Email recipients | `EMAIL_RECIPIENTS` | `user1@example.com,user2@example.com` |
| Email sender | `EMAIL_SENDER` | `noreply@yourdomain.com` |
| Mail server | `MAIL_SERVER` | `smtp.yourserver.com` |
| PowerCode API URL | `PC_URL` | `https://your-powercode-server.com` |
| Customer portal password | `CUSTOMER_PORTAL_PASSWORD` | `YourSecurePassword123` |

---

## Troubleshooting

### Application Won't Start

**Error: "Missing required environment variables"**
- Solution: Ensure all required variables are set in your `.env` file
- Check `.env.example` for the complete list
- Verify no typos in variable names

**Error: "No module named 'dotenv'"**
- Solution: Install python-dotenv: `pip install python-dotenv`

### SSL Certificate Errors

**Error: "SSL: CERTIFICATE_VERIFY_FAILED"**
- For PowerCode API: Set `PC_VERIFY_SSL=false` in `.env` (temporary workaround)
- Check that `PC_VERIFY_SSL` is set correctly

### Email Not Sending

- Verify `MAIL_SERVER` and `MAIL_PORT` are correct
- Check `EMAIL_SENDER` and `EMAIL_RECIPIENTS` format
- Ensure mail server allows connections from your IP
- Check application logs in `api_class.log`

### Configuration Not Loading

- Ensure `.env` file is in the same directory as `api_callback.py`
- Check file permissions on `.env`
- Verify `.env` file doesn't have a `.txt` extension
- Restart the application after changing `.env`

---
